"""Unit tests for toml.py."""
import io
from unittest.mock import mock_open, patch

from pypyr.context import Context
import pypyr.toml as toml


def test_toml_file_roundtrip():
    """Read toml file, edit it, dump it."""
    in_bytes = b"""[table]
foo = "bar"  # String
baz = 13

[table2]
array = [1, 2, 3]
"""

    # read
    with patch('pypyr.toml.open',
               mock_open(read_data=in_bytes)) as mocked_open:
        payload = toml.read_file('arb/path.in')

    mocked_open.assert_called_once_with('arb/path.in', 'rb')

    assert payload['table']['baz'] == 13
    assert payload['table2']['array'] == [1, 2, 3]

    # add like you would to a normall dict
    payload['table3'] = {'a': 'b', 'c': True}

    # write
    with io.BytesIO() as out_bytes:
        with patch('pypyr.toml.open', mock_open()) as mock_output:
            mock_output.return_value.write.side_effect = out_bytes.write
            toml.write_file('arb/out.toml', payload)
        out_str = out_bytes.getvalue().decode()

    mock_output.assert_called_once_with('arb/out.toml', 'wb')

    # round-tripped serialization has table3 as added from python dict obj
    assert out_str == """[table]
foo = "bar"
baz = 13

[table2]
array = [
    1,
    2,
    3,
]

[table3]
a = "b"
c = true
"""


def test_toml_context_interop():
    """Toml object works with pypyr Context."""
    in_bytes = b"""k1 = "v1"
    k2 = "start{k1}end"
    k3 = 3

    [table]
    array = [1, 2, "{k3}"]
    """

    # read
    with patch('pypyr.toml.open',
               mock_open(read_data=in_bytes)) as mocked_open:
        toml_obj = toml.read_file('arb/path.in')

    mocked_open.assert_called_once_with('arb/path.in', 'rb')

    # load toml obj into Context
    context = Context(toml_obj)

    # toml obj works with context formatting/merging methods
    assert context.get_formatted('k2') == 'startv1end'
    assert context.get_formatted_value(context['table']) == {'array':
                                                             [1, 2, 3]}

    context.merge({'table': {'array': [4, 5]}})
    assert context.get_formatted_value(context['table']['array']) == [1,
                                                                      2,
                                                                      3,
                                                                      4,
                                                                      5]
