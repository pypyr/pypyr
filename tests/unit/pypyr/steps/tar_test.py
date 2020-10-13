"""tar.py unit tests."""
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
import pypyr.steps.tar
import pytest
from unittest.mock import patch, DEFAULT

# ------------------------- get file mode ------------------------------------#


def test_get_file_mode_for_reading():
    """File Mode for reading passes, with defaults."""
    # if there's no tarFormat, r:*
    assert 'r:*' == pypyr.steps.tar.get_file_mode_for_reading({})

    # if there's a tarFormat, r:blah
    assert 'r:blah' == pypyr.steps.tar.get_file_mode_for_reading(
        {'format': 'blah'})


def test_get_file_mode_for_writing():
    """File Mode for writing passes, with defaults."""
    # if there's no tarFormat, r:*
    assert 'w:xz' == pypyr.steps.tar.get_file_mode_for_writing({})

    # if there's a tarFormat, r:blah
    assert 'w:blah' == pypyr.steps.tar.get_file_mode_for_writing(
        {'format': 'blah'})

# ------------------------- get file mode ------------------------------------#


# ------------------------- tar base -----------------------------------------#


def test_tar_throws_on_empty_context():
    """Context must exist."""
    with pytest.raises(AssertionError) as err_info:
        pypyr.steps.tar.run_step(None)

    assert str(err_info.value) == "context must have value for pypyr.steps.tar"


def test_tar_throws_if_all_tar_context_missing():
    """Tar context keys must exist."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.tar.run_step(Context({'arbkey': 'arbvalue'}))

    assert str(err_info.value) == ("context['tar'] doesn't exist. It must "
                                   "exist for pypyr.steps.tar.")


def test_tar_throws_if_tar_context_wrong_type():
    """Tar context keys must exist."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.tar.run_step(
            Context({'tar': {'extractX': 'it shouldnt be a string'}}))

    assert str(err_info.value) == (
        "pypyr.steps.tar must have either extract or archive specified under "
        "the tar key. Or both of these. It has neither.")


def test_tar_throws_if_tar_context_no_value():
    """Tar context keys must exist."""
    with pytest.raises(KeyNotInContextError) as err_info:
        pypyr.steps.tar.run_step(
            Context({'tar': {'extract': None,
                             'archive': None}}))

    assert str(err_info.value) == (
        "pypyr.steps.tar must have either extract or archive specified under "
        "the tar key. Or both of these. It has neither.")


def test_tar_only_calls_extract():
    """Only calls extract if only extract specified."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'tar': {'extract': [
            {'in': 'key2',
             'out': 'ARB_GET_ME1'},
            {'in': 'key4',
             'out': 'ARB_GET_ME2'}
        ]}
    })

    with patch.multiple('pypyr.steps.tar',
                        tar_archive=DEFAULT,
                        tar_extract=DEFAULT
                        ) as mock_tar:
        pypyr.steps.tar.run_step(context)

    mock_tar['tar_extract'].assert_called_once()
    mock_tar['tar_archive'].assert_not_called()


def test_tar_only_calls_archive():
    """Only calls archive if only archive specified."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'tar': {'archive': [
            {'in': 'key2',
             'out': 'ARB_GET_ME1'},
            {'in': 'key4',
             'out': 'ARB_GET_ME2'}
        ]}
    })

    with patch.multiple('pypyr.steps.tar',
                        tar_archive=DEFAULT,
                        tar_extract=DEFAULT
                        ) as mock_tar:
        pypyr.steps.tar.run_step(context)

    mock_tar['tar_extract'].assert_not_called()
    mock_tar['tar_archive'].assert_called_once()


def test_tar_calls_archive_and_extract():
    """Calls both extract and archive when both specified."""
    context = Context({
        'key2': 'value2',
        'key1': 'value1',
        'key3': 'value3',
        'tar': {'archive': [
            {'in': 'key2',
             'out': 'ARB_GET_ME1'},
            {'in': 'key4',
             'out': 'ARB_GET_ME2'}
        ],
            'extract': [
            {'in': 'key2',
             'out': 'ARB_GET_ME1'},
            {'in': 'key4',
             'out': 'ARB_GET_ME2'}
        ]}
    })

    with patch.multiple('pypyr.steps.tar',
                        tar_archive=DEFAULT,
                        tar_extract=DEFAULT
                        ) as mock_tar:
        pypyr.steps.tar.run_step(context)

    mock_tar['tar_extract'].assert_called_once()
    mock_tar['tar_archive'].assert_called_once()


# ------------------------- tar base   ---------------------------------------#
#
# ------------------------- tar extract---------------------------------------#

def test_tar_extract_one_pass():
    """Tar extract success case."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'tar': {'extract': [
            {'in': './blah.tar.xz',
             'out': 'path/to/dir'}
        ]}
    })

    with patch('tarfile.open') as mock_tarfile:
        pypyr.steps.tar.run_step(context)

    mock_tarfile.assert_called_once_with('./blah.tar.xz', 'r:*')
    (mock_tarfile.return_value.
     __enter__().extractall.assert_called_once_with('path/to/dir'))


def test_tar_extract_one_pass_uncompressed():
    """Tar extract success case."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'tar': {'extract': [
            {'in': './blah.tar.xz',
             'out': 'path/to/dir'}
        ],
            'format': ''}
    })

    with patch('tarfile.open') as mock_tarfile:
        pypyr.steps.tar.run_step(context)

    mock_tarfile.assert_called_once_with('./blah.tar.xz', 'r:')
    (mock_tarfile.return_value.
     __enter__().extractall.assert_called_once_with('path/to/dir'))


def test_tar_extract_one_with_interpolation():
    """Tar extract success case."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'tar': {'extract': [
            {'in': './{key3}.tar.xz',
             'out': 'path/{key2}/dir'}
        ]}
    })

    with patch('tarfile.open') as mock_tarfile:
        pypyr.steps.tar.run_step(context)

    mock_tarfile.assert_called_once_with('./value3.tar.xz', 'r:*')
    (mock_tarfile.return_value.
     __enter__().extractall.assert_called_once_with('path/value2/dir'))


def test_tar_extract_pass():
    """Tar extract success case."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'tar': {'extract': [
            {'in': './blah.tar.xz',
             'out': 'path/to/dir'},
            {'in': '/tra/la/la.tar.xz',
             'out': '.'}
        ]}
    })

    with patch('tarfile.open') as mock_tarfile:
        pypyr.steps.tar.run_step(context)

    assert mock_tarfile.call_count == 2
    mock_tarfile.assert_any_call('./blah.tar.xz', 'r:*')
    mock_tarfile.assert_any_call('/tra/la/la.tar.xz', 'r:*')
    (mock_tarfile.return_value.
     __enter__().extractall.call_count == 2)
    (mock_tarfile.return_value.
     __enter__().extractall.assert_any_call('path/to/dir'))
    (mock_tarfile.return_value.
     __enter__().extractall.assert_any_call('.'))

# ------------------------- tar extract---------------------------------------#

# ------------------------- tar archive---------------------------------------#


def test_tar_archive_one_pass():
    """Tar extract success case."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'tar': {'archive': [
            {'in': 'path/to/dir',
             'out': './blah.tar.xz'}
        ]}
    })

    with patch('tarfile.open') as mock_tarfile:
        pypyr.steps.tar.run_step(context)

    mock_tarfile.assert_called_once_with('./blah.tar.xz', 'w:xz')
    (mock_tarfile.return_value.
     __enter__().add.assert_called_once_with('path/to/dir', arcname='.'))


def test_tar_archive_one_pass_with_interpolation():
    """Tar extract success case."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'tar': {'archive': [
            {'in': '{key2}/to/dir',
             'out': './blah.tar.{key1}'}
        ]}
    })

    with patch('tarfile.open') as mock_tarfile:
        pypyr.steps.tar.run_step(context)

    mock_tarfile.assert_called_once_with('./blah.tar.value1', 'w:xz')
    (mock_tarfile.return_value.
     __enter__().add.assert_called_once_with('value2/to/dir', arcname='.'))


def test_tar_archive_one_pass_without_compression():
    """Tar extract success case without compression."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'tar': {'archive': [
            {'in': 'path/to/dir',
             'out': './blah.tar.xz'}
        ],
            'format': ''}
    })

    with patch('tarfile.open') as mock_tarfile:
        pypyr.steps.tar.run_step(context)

    mock_tarfile.assert_called_once_with('./blah.tar.xz', 'w:')
    (mock_tarfile.return_value.
     __enter__().add.assert_called_once_with('path/to/dir', arcname='.'))


def test_tar_archive_one_pass_with_gz():
    """Tar extract success case with gz."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'tarFormat': 'gz',
        'tar': {'archive': [
            {'in': 'path/to/dir',
             'out': './blah.tar.gz'}
        ],
            'format': '{tarFormat}'}
    })

    with patch('tarfile.open') as mock_tarfile:
        pypyr.steps.tar.run_step(context)

    mock_tarfile.assert_called_once_with('./blah.tar.gz', 'w:gz')
    (mock_tarfile.return_value.
     __enter__().add.assert_called_once_with('path/to/dir', arcname='.'))


def test_tar_archive_pass():
    """Tar extract success case."""
    context = Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'blah',
        'tar': {'archive': [
            {'in': 'path/to/dir',
             'out': './{key3}.tar.xz'},
            {'in': '.',
             'out': '/tra/la/la.tar.xz'}
        ]}
    })

    with patch('tarfile.open') as mock_tarfile:
        pypyr.steps.tar.run_step(context)

    assert mock_tarfile.call_count == 2
    mock_tarfile.assert_any_call('./blah.tar.xz', 'w:xz')
    mock_tarfile.assert_any_call('/tra/la/la.tar.xz', 'w:xz')
    (mock_tarfile.return_value.
     __enter__().add.call_count == 2)
    (mock_tarfile.return_value.
     __enter__().add.assert_any_call('path/to/dir', arcname='.'))
    (mock_tarfile.return_value.
     __enter__().add.assert_any_call('.', arcname='.'))

# ------------------------- tar archive --------------------------------------#
