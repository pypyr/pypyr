"""pypyr dynamic modules, namespaces and path discovery.

Load modules dynamically, find things on file-system.

Attributes:
    CWD (Path): Global shared current working dir.
"""
import ast
import builtins
from collections import ChainMap
import importlib
import logging
from pathlib import Path
import sys
from threading import Lock

from pypyr.errors import PyModuleNotFoundError

CWD = Path.cwd()

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


class _ChainMapPretendDict(ChainMap, dict):
    """It's a ChainMap. But it will pass an isinstance check for dict.

    Don't Use Me. Seriously.

    The only reason for this is to use as globals with eval/exec. Because
    eval/exec only accepts dict type as globals argument.

    However, for the purposes of pypyr, rather than make a whole copy of the
    context dict each and every time a py expression evaluates, it's much
    more performance efficient to use a chainmap to chain together the dynamic
    code's global namespace and context.

    That does not mean what you see here is a good idea. It's not. It's the
    least bad of other bad options.

    Don't pickle me. Re-instantiate instead.

    There are 2 storage mechanisms here:
    - the dict instance itself
    - the ChainMap maps attribute (a list of dicts, basically.)

    The ChainMap overrides most of the accessors you'd associate with dict
    (get, set, items, etc.) because it is 1st in the mro.

    See docs/adr/0001-namespace-on-eval-and-exec.md
    """

    __slots__ = ()

    def __init__(self, *maps):
        """Initialize the dict to builtins, and the chainmap to *maps.

        Args:
            maps: mapping dict-like objects to add to the chainmap.
        """
        dict.__setitem__(self, '__builtins__', builtins.__dict__)
        super().__init__(*maps)


class ImportVisitor(ast.NodeVisitor):
    """Parse python import and import from syntax.

    Use this to parse python syntax of import/import from, import the modules
    and save the result to the imported_namespace namespace dictionary.

    Only supports absolute imports, not relative. Does not support wildcard
    style 'from x import *'. But you weren't planning on doing *that* anyway,
    I hope.

    Supports source like:
        import x
        import x as y
        import x.y
        import x.y as z
        from x import y
        from x import y as z
        from x import y, z
        from a.b import c as d, e as f

    Usage example:
        ImportVisitor().visit(ast.parse('from mod.sub import attr as alias'))

    Will result in:
        imported_namespace == {'alias': <<attr in mod.sub module>>}

    Attributes:
        imported_namespace (dict): Namespace dictionary of imported references.
    """

    def __init__(self):
        """Initialize me."""
        self.imported_namespace = {}

    def get_namespace(self, source):
        """Parse source, import modules & return namespace.

        You might as well call this instead of visit().

        Args:
            source (str): String of Python source code.

        Return:
            Namespace dictionary of imported references.
        """
        self.visit(ast.parse(source))
        return self.imported_namespace

    def _set_namespace(self, alias, obj):
        """Add imported object to namespace dictionary.

        Args:
            alias (ast.alias): Use asname for alias if it exists, else fall
                back to name.
            obj (any): Imported module or attribute like class or function.

        Returns: None
        """
        as_name = alias.asname if alias.asname else alias.name
        self.imported_namespace[as_name] = obj

    def visit_Import(self, node):
        """Process syntax nodes of form: import module."""
        for alias in node.names:
            if alias.asname:
                imported_module = importlib.import_module(alias.name)
            else:
                # if no alias, 'import mod.sub' has to bind 'mod' to the
                # imported parent obj.
                parent, dot, _ = alias.name.partition('.')
                if dot:
                    # mod.sub1.sub2 should save to namespace as parent 'mod'
                    alias.asname = parent
                    # __import__(), although discouraged, is how to get the
                    # top-level module - this is the obj that is bound by the
                    # name in the namespace
                    imported_module = __import__(alias.name)
                else:
                    imported_module = importlib.import_module(alias.name)

            self._set_namespace(alias, imported_module)

    def visit_ImportFrom(self, node):
        """Process syntax nodes of form: from parent import child."""
        if node.level > 0:
            raise TypeError("you can't use relative imports here. "
                            "use absolute imports instead.")
        imported_module = importlib.import_module(node.module)
        for alias in node.names:
            try:
                imported_obj = getattr(imported_module, alias.name)
            except AttributeError:
                # if no attribute, might be form: from mod import submod
                imported_obj = importlib.import_module(
                    f'{node.module}.{alias.name}')

            self._set_namespace(alias, imported_obj)


_sys_path_lock = Lock()
_known_dirs = set()


def add_sys_path(path):
    """Add path to sys.path if it doesn't exist in sys.path already.

    Only add paths that actually exist.

    Do this under a shared lock to prevent duplicates in sys.path.

    _known_dirs does not mean a path exists, it means the logic around
    whether to add a path or not has run.

    Args:
        path (Path-like): path to add to sys.path
    """
    if path in _known_dirs:
        return

    path_obj = path if isinstance(path, Path) else Path(path)

    if not path_obj.exists():
        _known_dirs.add(path)
        return

    # sys path doesn't accept Path
    path_str = str(path_obj)  # .resolve(True)? instead for extended paths?
    logger.debug("adding %s to sys.paths", path_str)
    with _sys_path_lock:
        if path_str not in sys.path:
            # append not insert - don't overwrite user's prior sys.path
            sys.path.append(path_str)

    _known_dirs.add(path)


def get_module(module_abs_import):
    """Use importlib to get the module dynamically.

    Get instance of the module specified by the module_abs_import.
    This means that module_abs_import must be resolvable from this package.

    Args:
        module_abs_import: string. Absolute name of module to import.

    Raises:
        PyModuleNotFoundError: if module not found.

    """
    logger.debug("starting")
    logger.debug("loading module %s", module_abs_import)
    try:
        imported_module = importlib.import_module(module_abs_import)
        logger.debug("done")
        return imported_module
    except ModuleNotFoundError as err:
        if err.name != module_abs_import:
            extended_msg = (
                f'error importing module {err.name} in {module_abs_import}')
            logger.error("Couldn't import module %s in this module: %s",
                         err.name,
                         module_abs_import)
        else:
            extended_msg = (
                f"{module_abs_import}.py should be in your pipeline dir, or "
                "in your working dir, or it should be installed in the "
                "current python env."
                "\nIf you have 'package.sub.mod' your pipeline dir should "
                "contain ./package/sub/mod.py\n"
                "If you specified 'mymodulename', your pipeline dir should "
                "contain ./mymodulename.py\n"
                "If the module is not in your pipeline dir nor in the current "
                "working dir, it must exist in your current python env - so "
                "you should have run pip install or setup.py")
            logger.error("The module doesn't exist. "
                         "Looking for a file like this: %s",
                         module_abs_import)
        raise PyModuleNotFoundError(extended_msg) from err
