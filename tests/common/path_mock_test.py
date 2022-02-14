"""Unit tests for tests/common/path_mock.py."""
import os
from pathlib import Path
from unittest.mock import call, patch

from tests.common.path_mock import FakePath, MultiPath


def test_fake_path():
    """A FakePath behaves like a Path."""
    fp = FakePath('/arb')
    assert isinstance(fp, Path)
    assert isinstance(fp, os.PathLike)
    assert fp.__fspath__() == f'{os.sep}arb'
    assert str(fp) == f'{os.sep}arb'

    # mocked out methods don't touch the file system
    assert fp.exists() is False
    fp.mkdir()
    fp.mkdir(exist_ok=True)
    fp.mkdir(exist_ok=False, parents=True)
    assert fp.is_file() is False
    assert fp.is_dir() is False

    # delegate to underlying path
    assert fp.name == 'arb'
    fp.mock_instance.joinpath.assert_not_called()
    assert fp.joinpath('sub') == Path('/arb/sub')

    # calls recorded
    assert fp.mock.mock_calls == [call('/arb'),
                                  call().exists(),
                                  call().mkdir(),
                                  call().mkdir(exist_ok=True),
                                  call().mkdir(exist_ok=False, parents=True),
                                  call().is_file(),
                                  call().is_dir(),
                                  call().joinpath('sub')]

    # can use various mock assert helpers
    # mock_instance is same as return_value
    fp.mock.assert_called_once_with('/arb')
    fp.mock_instance.mkdir.assert_called_with(exist_ok=False,
                                              parents=True)
    fp.mock.return_value.joinpath.assert_called_once_with('sub')
    fp.mock.return_value.is_dir.assert_called_once()
    fp.mock_instance.is_dir.assert_called_once()


def test_fake_path_parent():
    """Methods returning Paths return FakePaths."""
    fp = FakePath('/arb/sub')
    parent = fp.parent
    assert fp.mock.mock_calls == [call('/arb/sub')]
    assert fp.mock.parent.mock_calls == []
    assert type(parent) is FakePath
    assert parent == Path('/arb')


def test_fake_path_constructor_overrides():
    """A FakePath with special values for is_dir, is_file."""
    # multi constructor
    fp = FakePath('arb', 'sub')
    assert fp == Path('arb/sub')

    f = FakePath('myfile', is_file=True)
    assert f.is_file() is True
    assert f.is_dir() is False
    assert f.exists() is True
    f.mock.assert_called_once_with('myfile')
    f.mock_instance.is_file.assert_called_once()

    d = FakePath('mydir', is_dir=True)
    assert d.is_dir() is True
    assert d.exists() is True
    d.mock.assert_called_once_with('mydir')
    d.mock_instance.is_file.assert_not_called()
    d.mock_instance.is_dir.assert_called_once()
    assert d.is_file() is False


def test_multi_fake_path():
    """Use multi path fakes with patch."""
    og_path_type = Path
    with patch('tests.common.path_mock_test.Path',
               new=MultiPath()) as mock_paths:
        p = Path('/arb')
        assert type(p) is FakePath
        assert isinstance(p, og_path_type)
        assert isinstance(p, Path)
        assert p.is_dir() is False
        assert p.is_file() is False
        assert p.exists() is False
        sp = p.joinpath('sub')
        sp2 = p.joinpath('sub', 'sub2')

        p2 = Path('/arb2')
        assert not p2.exists()

    assert sp == Path('/arb/sub')
    assert sp2 == Path('/arb/sub/sub2')

    assert len(mock_paths.instances) == 2
    assert mock_paths.instances[0].mock.mock_calls == [call('/arb'),
                                                       call().is_dir(),
                                                       call().is_file(),
                                                       call().exists(),
                                                       call().joinpath('sub'),
                                                       call().joinpath('sub',
                                                                       'sub2')]

    mock_paths.instances[1].mock.assert_called_once_with('/arb2')
    mock_paths.instances[1].mock.return_value.exists.assert_called_once()


def test_multi_fake_path_objs():
    """Multiple objects under the MultiPath scope."""
    with patch('tests.common.path_mock_test.Path',
               new=MultiPath()) as mock_paths:
        p = Path('/arb')
        assert not p.is_dir()
        assert not p.exists()
        assert not Path('arb2', 'sub2').is_file()

    assert mock_paths.instances[0].mock.mock_calls == [call('/arb'),
                                                       call().is_dir(),
                                                       call().exists()]

    assert mock_paths.instances[1].mock.mock_calls == [call('arb2', 'sub2'),
                                                       call().is_file()]


def test_multi_fake_path_with_known():
    """Use multi path fakes with patch and pre-configured known paths."""
    multi = MultiPath({'/arb': FakePath('/arb', is_dir=True),
                       ('arb2', 'sub2'): FakePath('/a/s', is_file=True)})

    with patch('tests.common.path_mock_test.Path', new=multi):
        p = Path('arb2', 'sub2')
        assert isinstance(p, Path)
        assert p.is_file()
        assert Path('/arb').is_dir()

    assert p == Path('/a/s')

    mock1 = multi.instances[0].mock
    mock1.assert_called_once_with('/a/s')
    mock1.return_value.is_file.assert_called_once()
    mock1.return_value.is_dir.assert_not_called()

    mock2 = multi.instances[1].mock
    mock2.assert_called_once_with('/arb')
    mock2.return_value.exists.assert_not_called()
    mock2.return_value.is_dir.assert_called_once()
