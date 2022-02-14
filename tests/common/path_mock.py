"""Mock the pathlib Path library.

Uses delegation to preserve most Path functionality, e.g building, joining &
str representation of paths, but bypass actual filesystem operations.

Similar to "wraps" on the built-in Mock/MagicMock object in that you log all
calls to the object, but with more control over which Path method calls also to
pass-through to the underlying wrapped object.

Because of Path actually being a factory object that constructs the concrete
PosixPath/WindowsPath, the built-in Mock with wraps+side_effect overrides on
the return_value doesn't work too well - as soon as you try to set the
return_value of the resulting path object, Python ignores wraps
(as documented).
"""
from pathlib import Path
from unittest.mock import Mock


class FakePath():
    """Delegates the pathlib.Path object.

    Behaves like a Path, pass instance checks as Path, logs all calls like a
    Mock does. Overrides select methods NOT to touch the filesystem, while
    still passing logical operations like .join or .parent to the delegated
    Path object.

    fp = FakePath('/arb)
    # is_file handled by FakePath, not passed through to filesystem
    fp.is_file()

    Track method calls to this fake path like this:
    fp.mock.assert_called_once_with('/arb')

    This:
    fp.mock_instance.is_file.assert_called_once()

    Is equivalent of:
    fp.mock.return_value.is_file.assert_called_once()

    Attributes:
        path (Path): The pathlib Path instance being delegated
        mock (Mock): A Mock containing all the calls to the Path.
        mock_instance (Mock): Convenient access to mock.return_value.
    """

    def __init__(self, *pathsegments, is_dir=False, is_file=False):
        """Construct a fake Path.

        p = FakePath('/arb')

        Will create a delegated Path('p) object under the covers, while the
        delegating FakePath will behave like the actual Path object without
        interacting with the actual file-system.

        Args:
            pathsegments: Input to the underlying Path() object ctor. is_dir
            (bool): Faked result of is_dir(). is_file (bool): Faked result of
            is_file().
        """
        self.path = Path(*pathsegments)
        mock = Mock(spec=type(self.path))
        self.mock = mock
        self.mock_instance = mock(*pathsegments)
        self._is_dir = is_dir
        self._is_file = is_file

        self._attr_mock_cache = {}

    @property
    def __class__(self):
        """Pretend to be PosixPath or WindowsPath, depending on os."""
        return type(self.path)

    def __eq__(self, other):
        """Allow equality check to work as per path."""
        return self.path == other

    def __instancecheck__(self, instance):
        """Allow me to masquerade as an actual Path object."""
        return isinstance(instance, Path)

    def __fspath__(self):
        """Implement os.PathLike interface."""
        return str(self.path)

    def exists(self):
        """Fake exists not actually to touch the filesystem.

        Returns: (bool)
            Is True if either is_dir or is_file is True.
        """
        self.mock_instance.exists()
        return self._is_dir or self._is_file

    def is_dir(self):
        """Fake is_dir not actually to touch the filesystem."""
        self.mock_instance.is_dir()
        return self._is_dir

    def is_file(self):
        """Fake is_file not actually to touch the filesystem."""
        self.mock_instance.is_file()
        return self._is_file

    def mkdir(self, *args, **kwargs):
        """Fake mkdir not actually to touch the filesystem."""
        self.mock_instance.mkdir(*args, **kwargs)

    def __getattr__(self, attr):
        """Delegate not found attrs to underlying path instance."""
        # Both mock the method call AND pass through to delegated Path method.
        # The attr name is unique for this object, so you can use the same mock
        # to log all calls to the same method.
        m = self._attr_mock_cache.get(attr, None)
        if m is None:
            m = Mock()()
            self._attr_mock_cache[attr] = m
            self.mock_instance.attach_mock(m, attr)

        underlying_attr = getattr(self.path, attr)

        if not callable(underlying_attr):
            return FakePath(underlying_attr) if isinstance(
                underlying_attr, Path) else underlying_attr

        # wrap the delegated callable so you can
        # capture the args+kwargs when callable
        # actually called
        def passthrough_wrapper(*args, **kwargs):
            m(*args, **kwargs)
            return underlying_attr(*args, **kwargs)

        return passthrough_wrapper

    def __str__(self):
        """Delegate str to underlying path object."""
        return str(self.path)


class MultiPath():
    """Use me as a `new` replacement on patch for multiple Path instantiations.

    This class will masquerade as a Path instance so this is True:
    isinstance(MultiPath(), Path)

    Use me like this:
        with patch('mymoduleundertest.Path', new=MultiPath()) as mock_path:
            do_things()

        # all the calls to the mock here, for your asserts etc.
        mock_path.instances[0].mock.mock_calls

    mock_path.instances contains all the mocked Path objects created in
            do_things() in order created.

    NB: use with "new" on patch, NOT with "side_effect".

    Attributes:
        instances (list): Instances of FakePath constructed under the patch
            scope, in order.
        known (dict): Cache of preconfigured FakePath to return when the
            input arguments match.
    """

    def __init__(self, known=None):
        """Construct the callable object to replace the patched Path.

        Use known to pre-configure FakePath instances for certain input
        arguments if you want to override FakePath defaults. The key of known
        is the pathsegments input of the Path call you want to mock.

        For example:
        {'p': FakePath(is_file=True), ('p1, 'p2): FakePath(is_dir=True)}

        This will use pre-created cached instances for:
            - Path('p')
            - Path('p1', 'p2)

        If you don't use known, will just create a FakePath with defaults.

        Args:
            known (dict): Cache of known FakePath instances mapped to their
                input args.
        """
        self.instances = []
        self.known = known if known else {}

    def __instancecheck__(self, instance):
        """Trick me into passing Path isinstance checks."""
        return isinstance(instance, FakePath)

    @property
    def __class__(self):
        """Trick me into looking like a Path."""
        return FakePath

    def __call__(self, *p):
        """Call this everytime the patched object instantiates.

        Will return either a new default FakePath or a cached FakePath from
        self.known if *p matches on each invocation.

        Args:
            *p: pathsegments input for mocked Path object.

        Returns:
            FakePath instance.
        """
        # this allows cache to hit on Path('one', 'two') and Path('one')
        fp = self.known.get(p[0]) if len(p) == 1 else self.known.get(p)
        if not fp:
            fp = FakePath(*p)

        self.instances.append(fp)
        return fp
