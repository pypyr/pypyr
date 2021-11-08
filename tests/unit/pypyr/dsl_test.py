"""dsl.py unit tests."""
from copy import deepcopy
from io import StringIO
import logging
import pytest
from unittest.mock import call, patch, MagicMock
from tests.common.utils import DeepCopyMagicMock, patch_logger

import ruamel.yaml as yamler
from ruamel.yaml.comments import CommentedMap, CommentedSeq, TaggedScalar

import pypyr.cache.stepcache as stepcache
from pypyr.context import Context
from pypyr.dsl import (Jsonify,
                       PyString,
                       SicString,
                       SpecialTagDirective,
                       Step,
                       RetryDecorator,
                       WhileDecorator)
from pypyr.errors import (Call,
                          HandledError,
                          LoopMaxExhaustedError,
                          PipelineDefinitionError)


def arb_step_mock(context):
    """No real reason, other than to mock the existence of a run_step."""
    return 'from arb step mock'
# region custom yaml tags

# region SpecialTagDirective base


def test_special_tag_directive_base_no_get_value():
    """Base class SpecialTagDirective raises on get_value."""
    base = SpecialTagDirective(None)

    with pytest.raises(NotImplementedError):
        base.get_value()


def test_special_tag_directive_base_eq():
    """Repr equivalence and inverse works."""
    assert SpecialTagDirective(None) == SpecialTagDirective(None)
    assert SpecialTagDirective('none') != SpecialTagDirective('some')


def test_special_tag_directive_repr_roundtrip():
    """Repr string repr evals back to instance."""
    s = SpecialTagDirective('arb')
    repr_string = repr(s)
    assert repr_string == 'SpecialTagDirective(\'arb\')'
    reconstituted = eval(repr_string)
    assert isinstance(reconstituted, SpecialTagDirective)
    assert str(reconstituted) == 'arb'


def test_special_tag_directive_truthy():
    """Special Tag String work as falsy, else Truthy."""
    assert SpecialTagDirective('blah')
    assert not SpecialTagDirective(None)
    assert not SpecialTagDirective('')

# endregion SpecialTagDirective base

# region jsonify custom tag


def test_jsonify_behaves():
    """Jsonify does what it should."""
    assert Jsonify.yaml_tag == '!jsonify'
    jsonify = Jsonify({'a': 'string here', 'b': 123, 'c': False})
    assert jsonify == Jsonify({'a': 'string here', 'b': 123, 'c': False})
    assert jsonify
    assert str(jsonify) == "{'a': 'string here', 'b': 123, 'c': False}"
    assert repr(jsonify) == (
        "Jsonify({'a': 'string here', 'b': 123, 'c': False})")
    assert jsonify.get_value(Context({'a': 'BBB'})) == (
        '{"a": "string here", "b": 123, "c": false}')


def get_yaml_jsonify_parser():
    """Create ruamel yaml parser with jsonify tag handler."""
    yaml_parser = yamler.YAML(typ='rt', pure=True)
    yaml_parser.register_class(Jsonify)
    return yaml_parser


def get_yaml_with_jsonify(input_string):
    """Get yaml from yaml parser with jsonify tag."""
    return get_yaml_jsonify_parser().load(input_string)


def get_string_from_yaml_with_jsonify(yaml):
    """Serialize yaml object to string."""
    stream = StringIO()
    get_yaml_jsonify_parser().dump(yaml, stream)
    output = stream.getvalue()
    stream.close()
    return output


def test_jsonify_roundtrip_mapping():
    """Jsonify serializes and deserializes from yaml mapping."""
    yaml_string = """\
              a: 1
              b: '1'
              c: !jsonify
                c1: v1
                c2: 22
                c3: 123.45
              d: False
              """
    yaml = get_yaml_with_jsonify(yaml_string)

    assert type(yaml['c']) is Jsonify
    assert type(yaml['c'].value) is CommentedMap
    assert repr(yaml['c']) == f"Jsonify({yaml['c'].value!r})"

    assert yaml['c'].value == {'c1': 'v1', 'c2': 22, 'c3': 123.45}
    assert yaml['c'].get_value(Context()) == (
        '{"c1": "v1", "c2": 22, "c3": 123.45}')

    roundtripped_string = get_string_from_yaml_with_jsonify(yaml)
    expected = (
        "a: 1\n"
        "b: '1'\n"
        "c: !jsonify\n"
        "  c1: v1\n"
        "  c2: 22\n"
        "  c3: 123.45\n"
        "d: false\n")

    assert roundtripped_string == expected


def test_jsonify_roundtrip_sequence():
    """Jsonify serializes and de-serializes from yaml sequence."""
    yaml_string = """\
              a: 1
              b: '1'
              c: !jsonify
                - v1
                - 22
                - 123.45
                - a: a value
                  b: 123
              d: False
              """
    yaml = get_yaml_with_jsonify(yaml_string)

    assert type(yaml['c']) is Jsonify
    assert type(yaml['c'].value) is CommentedSeq
    assert repr(yaml['c']) == f"Jsonify({yaml['c'].value!r})"

    assert yaml['c'].value == ['v1',
                               22,
                               123.45,
                               {'a': 'a value',
                                'b': 123}]

    assert yaml['c'].get_value(Context()) == (
        '["v1", 22, 123.45, {"a": "a value", "b": 123}]')

    roundtripped_string = get_string_from_yaml_with_jsonify(yaml)
    expected = (
        "a: 1\n"
        "b: '1'\n"
        "c: !jsonify\n"
        "- v1\n"
        "- 22\n"
        "- 123.45\n"
        "- a: a value\n"
        "  b: 123\n"
        "d: false\n")

    assert roundtripped_string == expected


def test_jsonify_roundtrip_scalar():
    """Jsonify serializes and de-serializes from yaml scalar."""
    yaml_string = """\
              a: 1
              b: '1'
              c: !jsonify my scalar
              d: !jsonify False
              e: !jsonify 123
              f: !jsonify '123'
              """
    yaml = get_yaml_with_jsonify(yaml_string)

    assert type(yaml['c']) is Jsonify
    assert yaml['c'].value == 'my scalar'
    assert type(yaml['c'].scalar) is TaggedScalar
    assert repr(yaml['c']) == f"Jsonify('my scalar', {yaml['c'].scalar!r})"
    assert yaml['d'].value is False
    assert repr(yaml['d']) == f"Jsonify(False, {yaml['d'].scalar!r})"
    assert yaml['e'].value == 123
    assert repr(yaml['e']) == f"Jsonify(123, {yaml['e'].scalar!r})"
    assert yaml['f'].value == '123'
    assert repr(yaml['f']) == f"Jsonify('123', {yaml['f'].scalar!r})"

    assert yaml['c'].get_value(Context()) == '"my scalar"'
    assert yaml['d'].get_value(Context()) == 'false'
    assert yaml['e'].get_value(Context()) == '123'
    assert yaml['f'].get_value(Context()) == '"123"'

    roundtripped_string = get_string_from_yaml_with_jsonify(yaml)
    expected = (
        "a: 1\n"
        "b: '1'\n"
        "c: !jsonify my scalar\n"
        "d: !jsonify False\n"
        "e: !jsonify 123\n"
        "f: !jsonify '123'\n")

    assert roundtripped_string == expected


def test_jsonify_roundtrip_mapping_substitutions():
    """Jsonify serializes & deserializes yaml mapping with substitutions."""
    yaml_string = """\
              a: 1
              b: '1'
              c: !jsonify
                c1: 'v{k3}'
                c2: 22
                c3: '{k2}'
                c4: "{k1} b"
                c5: '{k4}'
              d: False
              """
    yaml = get_yaml_with_jsonify(yaml_string)

    context = Context({'k1': 'string {here}',
                       'k2': 123.45,
                       'k3': 1,
                       'k4': '{k2}'})
    assert type(yaml['c']) is Jsonify
    assert type(yaml['c'].value) is CommentedMap
    assert repr(yaml['c']) == f"Jsonify({yaml['c'].value!r})"

    assert yaml['c'].value == {'c1': 'v{k3}',
                               'c2': 22,
                               'c3': '{k2}',
                               'c4': '{k1} b',
                               'c5': '{k4}'}

    expected_json = (
        '{"c1": "v1", "c2": 22, "c3": 123.45, "c4": "string {here} b", '
        '"c5": 123.45}')
    assert yaml['c'].get_value(context) == expected_json

    roundtripped_string = get_string_from_yaml_with_jsonify(yaml)
    expected = (
        "a: 1\n"
        "b: '1'\n"
        "c: !jsonify\n"
        "  c1: v{k3}\n"
        "  c2: 22\n"
        "  c3: '{k2}'\n"
        "  c4: '{k1} b'\n"
        "  c5: '{k4}'\n"
        "d: false\n")

    assert roundtripped_string == expected


def test_jsonify_roundtrip_sequence_substitutions():
    """Jsonify serializes & de-serializes yaml sequence with substitutions."""
    yaml_string = """\
              a: 1
              b: '1'
              c: !jsonify
                - v{k3}
                - 22
                - "{k2}"
                - a: a value
                  b: '{k4}'
              d: False
              """
    yaml = get_yaml_with_jsonify(yaml_string)

    context = Context({'k1': 'string {here}',
                       'k2': 123.45,
                       'k3': 1,
                       'k4': '{k2}'})

    assert type(yaml['c']) is Jsonify
    assert type(yaml['c'].value) is CommentedSeq
    assert repr(yaml['c']) == f"Jsonify({yaml['c'].value!r})"

    assert yaml['c'].value == ['v{k3}',
                               22,
                               '{k2}',
                               {'a': 'a value',
                                'b': '{k4}'}]

    assert yaml['c'].get_value(context) == (
        '["v1", 22, 123.45, {"a": "a value", "b": 123.45}]')

    roundtripped_string = get_string_from_yaml_with_jsonify(yaml)
    expected = (
        "a: 1\n"
        "b: '1'\n"
        "c: !jsonify\n"
        "- v{k3}\n"
        "- 22\n"
        "- '{k2}'\n"
        "- a: a value\n"
        "  b: '{k4}'\n"
        "d: false\n")

    assert roundtripped_string == expected


def test_jsonify_roundtrip_scalar_substitutions():
    """Jsonify serializes & de-serializes yaml scalar with substitutions."""
    yaml_string = """\
              a: 1
              b: '1'
              c: !jsonify '{k1}'
              d: !jsonify '{k2}'
              e: !jsonify '{k3}'
              f: !jsonify b {k4}
              """
    yaml = get_yaml_with_jsonify(yaml_string)

    context = Context({'k1': 'my scalar',
                       'k2': False,
                       'k3': 123,
                       'k4': 'a {k1}'})

    assert type(yaml['c']) is Jsonify
    assert yaml['c'].value == '{k1}'
    assert type(yaml['c'].scalar) is TaggedScalar
    assert repr(yaml['c']) == f"Jsonify('{{k1}}', {yaml['c'].scalar!r})"
    assert yaml['d'].value == '{k2}'
    assert yaml['e'].value == '{k3}'
    assert yaml['f'].value == 'b {k4}'

    assert yaml['c'].get_value(context) == '"my scalar"'
    assert yaml['d'].get_value(context) == 'false'
    assert yaml['e'].get_value(context) == '123'
    assert yaml['f'].get_value(context) == '"b a {k1}"'

    roundtripped_string = get_string_from_yaml_with_jsonify(yaml)
    expected = (
        "a: 1\n"
        "b: '1'\n"
        "c: !jsonify '{k1}'\n"
        "d: !jsonify '{k2}'\n"
        "e: !jsonify '{k3}'\n"
        "f: !jsonify b {k4}\n")

    assert roundtripped_string == expected

# endregion jsonify custom tag

# region py string custom tag


def test_py_string_behaves():
    """Py string does what it should."""
    assert PyString.yaml_tag == '!py'
    py = PyString('1+1')
    assert str(py) == '1+1'
    assert repr(py) == "PyString('1+1')"
    assert py.get_value(Context()) == 2


def test_py_string_class_methods():
    """Py string yaml class methods serialize and deserialize class."""
    mock_node = MagicMock()
    mock_node.value = 'False and False'

    new_instance = PyString.from_yaml(None, mock_node)
    assert isinstance(new_instance, PyString)
    assert str(new_instance) == 'False and False'
    assert repr(new_instance) == "PyString('False and False')"
    assert not new_instance.get_value(Context())

    mock_representer = MagicMock()
    PyString.to_yaml(mock_representer, mock_node)
    mock_representer.represent_scalar.assert_called_once_with('!py',
                                                              'False and False'
                                                              )


def test_py_string_with_context():
    """Py string works with Context."""
    assert PyString('len(a)').get_value(Context({'a': '123'})) == 3


def test_py_string_with_imports():
    """Py string can use imported global namespace."""
    context = Context({'a': -3, 'b': 4})
    from math import sqrt
    context.pystring_globals_update({'squareroot': sqrt})
    assert PyString('abs(a) + squareroot(b)').get_value(context) == 5
    # imports don't end up in context
    assert context == {'a': -3, 'b': 4}
    # imports don't contain builtins
    assert context._pystring_globals == {'squareroot': sqrt}


def test_py_string_with_closure_scope():
    """Free variables resolve."""
    # NameError b is not defined if not a single global scope.
    # Just 'a' will work, it's the nested scope that's the prob
    source = "[f'{x}{y}' for x in a for y in b]"
    context = Context({'a': '12', 'b': 'ab'})
    assert PyString(source).get_value(context) == ['1a', '1b', '2a', '2b']
    # should contain nothing because nothing added to global as part of eval.
    assert context._pystring_globals == {}
    # context not polluted.
    assert context == {'a': '12', 'b': 'ab'}


def test_py_string_eq_and_neq():
    """Py string equivalence passes on repr."""
    assert PyString('arb') == PyString('arb')
    assert PyString('blah') != PyString('arb')


def test_py_string_repr_roundtrip():
    """Py string repr evals back to instance."""
    s = PyString('len("three")')
    repr_string = repr(s)
    assert repr_string == 'PyString(\'len("three")\')'
    reconstituted = eval(repr_string)
    assert isinstance(reconstituted, PyString)
    assert reconstituted.get_value(Context()) == 5


def test_py_string_empty():
    """Empty py string raises error."""
    with pytest.raises(ValueError) as err:
        PyString(None).get_value({})

    assert str(err.value) == ('!py string expression is empty. It must be a '
                              'valid python expression instead.')

    with pytest.raises(ValueError) as err:
        PyString('').get_value(Context())


def test_py_string_truthy():
    """Empty Py String work as falsy, else Truthy."""
    assert PyString('blah')
    assert not PyString(None)
    assert not PyString('')

# endregion py string custom tag

# region sic string custom tag


def test_sic_string_behaves():
    """Sic string does what it should."""
    assert SicString.yaml_tag == '!sic'
    sic = SicString('1+1')
    assert str(sic) == '1+1'
    assert repr(sic) == "SicString('1+1')"
    assert sic.get_value({}) == '1+1'


def test_sic_string_class_methods():
    """Sic string yaml class methods serialize and deserialize class."""
    mock_node = MagicMock()
    mock_node.value = 'False {and} False'

    new_instance = SicString.from_yaml(None, mock_node)
    assert isinstance(new_instance, SicString)
    assert str(new_instance) == 'False {and} False'
    assert repr(new_instance) == "SicString('False {and} False')"
    assert new_instance.get_value({}) == 'False {and} False'

    mock_representer = MagicMock()
    SicString.to_yaml(mock_representer, mock_node)
    mock_representer.represent_scalar.assert_called_once_with(
        '!sic',
        'False {and} False'
    )


def test_sic_string_with_context():
    """Sic string works with Context."""
    assert SicString('len(a)').get_value(Context({'a': '123'})) == 'len(a)'


def test_sic_string_eq_and_neq():
    """Sic string equivalence passes on repr."""
    assert SicString('arb') == SicString('arb')
    assert SicString('blah') != SicString('arb')


def test_sic_string_repr_roundtrip():
    """Sic string repr evals back to instance."""
    s = SicString('arb')
    repr_string = repr(s)
    assert repr_string == "SicString('arb')"
    reconstituted = eval(repr_string)
    assert isinstance(reconstituted, SicString)
    assert reconstituted.get_value() == 'arb'


def test_sic_string_truthy():
    """Empty Sic String work as falsy, else Truthy."""
    assert SicString('blah')
    assert not SicString(None)
    assert not SicString('')

# endregion sic string custom tag

# endregion custom yaml tags

# region test setup & fixtures
# region test context


def get_test_context():
    """Return a pypyr context for testing."""
    return Context({
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key4': [
            {'k4lk1': 'value4',
             'k4lk2': 'value5'},
            {'k4lk1': 'value6',
             'k4lk2': 'value7'}
        ],
        'key5': False,
        'key6': True,
        'key7': 77
    })

# endregion test context

# region step mocks


def mock_run_step(context):
    """Arbitrary mock function to execute instead of run_step."""
    context['test_run_step'] = 'this was set in step'


def mock_run_step_empty_context(context):
    """Clear the context in the step."""
    context.clear()


def mock_run_step_none_context(context):
    """None the context in the step."""
    # ignore the context is not used flake8 warning
    context = None  # noqa: F841
# endregion step mocks

# endregion test setup & fixtures

# region Step
# region Step: init


@patch('pypyr.moduleloader.get_module')
def test_simple_step_init_defaults(mocked_moduleloader):
    """Simple step initializes with defaults as expected."""
    mocked_moduleloader.return_value.run_step = arb_step_mock

    with patch_logger('pypyr.dsl') as mock_logger_debug:
        step = Step('blah')

    mock_logger_debug.assert_any_call("blah is a simple string.")

    assert step.name == 'blah'
    assert step.run_step_function('blahblah') == 'from arb step mock'
    assert step.foreach_items is None
    assert not hasattr(step, 'for_counter')
    assert step.in_parameters is None
    assert not step.retry_decorator
    assert step.run_me
    assert not step.skip_me
    assert not step.swallow_me
    assert not step.while_decorator
    assert step.line_no is None
    assert step.line_col is None

    mocked_moduleloader.assert_called_once_with('blah')


@patch('pypyr.moduleloader.get_module')
def test_complex_step_init_defaults(mocked_moduleloader):
    """Complex step initializes with defaults as expected."""
    stepcache.step_cache.clear()
    mocked_moduleloader.return_value.run_step = arb_step_mock
    with patch_logger('pypyr.dsl') as mock_logger_debug:
        step = Step({'name': 'blah'})

    assert mock_logger_debug.call_args_list == [
        call("starting"),
        call("blah is complex."),
        call("step name: blah"),
        call("done"),
    ]

    assert step.name == 'blah'
    assert step.run_step_function('blahblah') == 'from arb step mock'
    assert step.foreach_items is None
    assert not hasattr(step, 'for_counter')
    assert step.in_parameters is None
    assert not step.retry_decorator
    assert step.run_me
    assert not step.skip_me
    assert not step.swallow_me
    assert not step.while_decorator
    assert step.line_col is None
    assert step.line_no is None

    mocked_moduleloader.assert_called_once_with('blah')


def test_complex_step_init_with_missing_name_round_trip():
    """Step can't get step name from the yaml pipeline."""
    with pytest.raises(PipelineDefinitionError) as err_info:
        with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
            step_info = CommentedMap({})
            step_info._yaml_set_line_col(6, 7)
            Step(step_info)

    assert mock_logger_error.call_count == 1
    assert mock_logger_error.mock_calls == [
        call('Error at pipeline step yaml line: 7, col: 8'),
    ]

    assert str(err_info.value) == "step must have a name."


@patch('pypyr.moduleloader.get_module', return_value=3)
def test_step_cant_get_run_step_dynamically(mocked_moduleloader):
    """Step can't get run_step method on the dynamically imported module."""
    stepcache.step_cache.clear()
    with pytest.raises(AttributeError) as err_info:
        with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
            with patch_logger('pypyr.cache.stepcache',
                              logging.ERROR) as mock_cache_logger_error:
                Step('mocked.step')

    mocked_moduleloader.assert_called_once_with('mocked.step')

    mock_logger_error.assert_called_once_with(
        'Error at pipeline step mocked.step')

    mock_cache_logger_error.assert_called_once_with(
        "The step mocked.step in module 3 doesn't have a "
        "run_step(context) function.")

    assert str(err_info.value) == "'int' object has no attribute 'run_step'"


@patch('pypyr.moduleloader.get_module', return_value=3)
def test_step_cant_get_run_step_dynamically_round_trip(mocked_moduleloader):
    """Step can't get run_step method on the dynamically imported module.

    With round trip yaml loaded context.
    """
    stepcache.step_cache.clear()
    with pytest.raises(AttributeError) as err_info:
        with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
            with patch_logger('pypyr.cache.stepcache',
                              logging.ERROR) as mock_cache_logger_error:
                commented_context = CommentedMap({'name': 'mocked.step'})
                commented_context._yaml_set_line_col(1, 2)
                Step(commented_context)

    mocked_moduleloader.assert_called_once_with('mocked.step')
    mock_logger_error.assert_called_once_with(
        "Error at pipeline step mocked.step yaml line: 2, col: 3")
    mock_cache_logger_error.assert_called_once_with(
        "The step mocked.step in module 3 doesn't have a "
        "run_step(context) function.")

    assert str(err_info.value) == "'int' object has no attribute 'run_step'"


@patch('pypyr.moduleloader.get_module')
def test_complex_step_init_with_decorators(mocked_moduleloader):
    """Complex step initializes with decorators set."""
    stepcache.step_cache.clear()
    mocked_moduleloader.return_value.run_step = arb_step_mock
    step = Step({'name': 'blah',
                 'in': {'k1': 'v1', 'k2': 'v2'},
                 'foreach': [0],
                 'retry': {'max': 5, 'sleep': 7},
                 'run': False,
                 'skip': True,
                 'swallow': True,
                 'while': {'stop': 'stop condition',
                           'errorOnMax': True,
                           'sleep': 3,
                           'max': 4}
                 })
    assert step.name == 'blah'
    assert step.run_step_function('blah') == 'from arb step mock'
    assert step.foreach_items == [0]
    assert step.foreach_items == [0]
    assert step.in_parameters == {'k1': 'v1', 'k2': 'v2'}
    assert step.retry_decorator.max == 5
    assert step.retry_decorator.sleep == 7
    assert step.retry_decorator.retry_counter is None
    assert not step.run_me
    assert step.skip_me
    assert step.swallow_me
    assert step.while_decorator.stop == 'stop condition'
    assert step.while_decorator.error_on_max
    assert step.while_decorator.sleep == 3
    assert step.while_decorator.max == 4
    assert step.while_decorator.while_counter is None

    mocked_moduleloader.assert_called_once_with('blah')


@patch('pypyr.moduleloader.get_module')
def test_complex_step_init_with_decorators_roundtrip(mocked_moduleloader):
    """Complex step initializes with decorators.

    Set with round trip yaml loaded context.
    """
    stepcache.step_cache.clear()
    mocked_moduleloader.return_value.run_step = arb_step_mock

    context = CommentedMap({
        'name': 'blah',
        'in': {'k1': 'v1', 'k2': 'v2'},
        'foreach': [0],
        'retry': {'max': 5, 'sleep': 7},
        'run': False,
        'skip': True,
        'swallow': True,
        'while': {
            'stop': 'stop condition',
            'errorOnMax': True,
            'sleep': 3,
            'max': 4
        }
    }
    )

    context._yaml_set_line_col(8, 9)

    step = Step(context)
    assert step.name == 'blah'
    assert step.run_step_function('blah') == 'from arb step mock'
    assert step.foreach_items == [0]
    assert step.for_counter is None
    assert step.in_parameters == {'k1': 'v1', 'k2': 'v2'}
    assert step.retry_decorator.max == 5
    assert step.retry_decorator.sleep == 7
    assert step.retry_decorator.retry_counter is None
    assert not step.run_me
    assert step.skip_me
    assert step.swallow_me
    assert step.while_decorator.stop == 'stop condition'
    assert step.while_decorator.error_on_max
    assert step.while_decorator.sleep == 3
    assert step.while_decorator.max == 4
    assert step.while_decorator.while_counter is None
    assert step.line_no == 9
    assert step.line_col == 10

    mocked_moduleloader.assert_called_once_with('blah')


# endregion Step: init

# region Step: description
@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_description(mock_invoke_step,
                                                     mock_get_module):
    """Complex step with run decorator outputs notify description."""
    step = Step({'name': 'step1',
                 'description': 'test {key1} description'})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.NOTIFY) as mock_logger_notify:
        step.run_step(context)

    mock_logger_notify.assert_called_once_with('test value1 description')
    mock_invoke_step.assert_called_once()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_description_not_run(mock_invoke_step,
                                                             mock_get_module):
    """Complex step with run decorator set false doesn't run step."""
    step = Step({'name': 'step1',
                 'description': 'test description',
                 'run': '{key5}'})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with patch_logger('pypyr.dsl', logging.NOTIFY) as mock_logger_notify:
            step.run_step(context)

    mock_logger_notify.assert_called_once_with('(skipping): test description')
    mock_logger_info.assert_any_call("step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_description_in_params(
        mock_invoke_step, mock_get_module):
    """Complex step with run decorator set false at the in parameters."""
    step = Step({'name': 'step1',
                 'description': 'test description',
                 'run': '{key5}',
                 'in': {'key5': True}})

    context = Context({"key5": False})

    with patch_logger('pypyr.dsl', logging.NOTIFY) as mock_logger_notify:
        step.run_step(context)

    mock_logger_notify.assert_called_once_with('test description')
    mock_invoke_step.assert_called_once()

    # validate all the in params ended up in context as intended
    assert len(context) == 0


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_description_skip(mock_invoke_step,
                                                          mock_get_module):
    """Complex step with run decorator set false doesn't run step."""
    step = Step({'name': 'step1',
                 'description': 'test {key5} description',
                 'skip': True})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with patch_logger('pypyr.dsl', logging.NOTIFY) as mock_logger_notify:
            step.run_step(context)

    mock_logger_notify.assert_called_once_with(
        '(skipping): test False description')
    mock_logger_info.assert_any_call("step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len

# endregion Step: description
# region Step: run_step: foreach


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'run_conditional_decorators')
@patch.object(Step, 'foreach_loop')
def test_foreach_none(mock_foreach, mock_run, mock_moduleloader):
    """Simple step with None foreach decorator doesn't loop."""
    step = Step('step1')

    context = get_test_context()
    original_len = len(context)

    step.run_step(context)

    mock_foreach.assert_not_called()

    mock_run.assert_called_once_with(get_test_context())

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'run_conditional_decorators')
@patch.object(Step, 'foreach_loop')
def test_foreach_empty(mock_foreach, mock_run, mock_moduleloader):
    """Complex step with empty foreach decorator doesn't loop."""
    step = Step({'name': 'step1',
                 'foreach': []})

    context = get_test_context()
    original_len = len(context)

    step.run_step(context)

    mock_foreach.assert_not_called()
    mock_run.assert_called_once_with(get_test_context())

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'run_conditional_decorators')
def test_foreach_once(mock_run, mock_moduleloader):
    """The foreach loops once."""
    step = Step({'name': 'step1',
                 'foreach': ['one']})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('foreach: running step one'),
        call('foreach decorator looped 1 times.')]

    assert mock_run.call_count == 1
    mutated_context = get_test_context()
    mutated_context['i'] = 'one'
    mock_run.assert_called_once_with(mutated_context)

    # validate all the in params ended up in context as intended, plus i
    assert len(context) == original_len + 1
    assert context['i'] == 'one'
    assert step.for_counter == 'one'
    assert step.for_counter == 'one'


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'run_conditional_decorators')
@patch('unittest.mock.MagicMock', new=DeepCopyMagicMock)
def test_foreach_twice(mock_run, mock_moduleloader):
    """The foreach loops twice."""
    step = Step({'name': 'step1',
                 'foreach': ['one', 'two']})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('foreach: running step one'),
        call('foreach: running step two'),
        call('foreach decorator looped 2 times.')]

    assert mock_run.call_count == 2
    mutated_context = get_test_context()
    mutated_context['i'] = 'one'

    mock_run.assert_any_call(mutated_context)

    mutated_context['i'] = 'two'
    mock_run.assert_any_call(mutated_context)

    # validate all the in params ended up in context as intended, plus i
    assert len(context) == original_len + 1
    # after the looping's done, the i value will be the last iterator value
    assert context['i'] == 'two'
    assert step.for_counter == 'two'


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'run_conditional_decorators')
@patch('unittest.mock.MagicMock', new=DeepCopyMagicMock)
def test_foreach_thrice_with_substitutions(mock_run, mock_moduleloader):
    """The foreach loops thrice with substitutions inside a list."""
    step = Step({'name': 'step1',
                 'foreach': ['{key1}', '{key2}', 'key3']})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('foreach: running step value1'),
        call('foreach: running step value2'),
        call('foreach: running step key3'),
        call('foreach decorator looped 3 times.')]

    assert mock_run.call_count == 3
    mutated_context = get_test_context()
    mutated_context['i'] = 'value1'

    mock_run.assert_any_call(mutated_context)

    mutated_context['i'] = 'value2'
    mock_run.assert_any_call(mutated_context)

    mutated_context['i'] = 'key3'
    mock_run.assert_any_call(mutated_context)

    # validate all the in params ended up in context as intended, plus i
    assert len(context) == original_len + 1
    # after the looping's done, the i value will be the last iterator value
    assert context['i'] == 'key3'
    assert step.for_counter == 'key3'


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'run_conditional_decorators')
@patch('unittest.mock.MagicMock', new=DeepCopyMagicMock)
def test_foreach_with_single_key_substitution(mock_run, mock_moduleloader):
    """The foreach gets list from string format expression."""
    step = Step({'name': 'step1',
                 'foreach': '{list}'})

    context = get_test_context()
    context['list'] = [99, True, 'string here', 'formatted {key1}']
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('foreach: running step 99'),
        call('foreach: running step True'),
        call('foreach: running step string here'),
        call('foreach: running step formatted value1'),
        call('foreach decorator looped 4 times.')]

    assert mock_run.call_count == 4
    mutated_context = get_test_context()
    mutated_context['list'] = [99, True, 'string here', 'formatted {key1}']

    mutated_context['i'] = 99
    mock_run.assert_any_call(mutated_context)

    mutated_context['i'] = True
    mock_run.assert_any_call(mutated_context)

    mutated_context['i'] = 'string here'
    mock_run.assert_any_call(mutated_context)

    mutated_context['i'] = 'formatted value1'
    mock_run.assert_any_call(mutated_context)

    # validate all the in params ended up in context as intended, plus i
    assert len(context) == original_len + 1
    # after the looping's done, the i value will be the last iterator value
    assert context['i'] == 'formatted value1'
    assert step.for_counter == 'formatted value1'


def mock_step_mutating_run(context):
    """Mock a step's run_step by setting a context value False."""
    context['dynamic_run_expression'] = False


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=mock_step_mutating_run)
def test_foreach_evaluates_run_decorator(mock_invoke, mock_moduleloader):
    """The foreach evaluates run_me expression on each loop iteration."""
    step = Step({'name': 'step1',
                 'run': '{dynamic_run_expression}',
                 'foreach': ['{key1}', '{key2}', 'key3']})

    context = get_test_context()
    context['dynamic_run_expression'] = True
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('foreach: running step value1'),
        call('foreach: running step value2'),
        call('step1 not running because run is False.'),
        call('foreach: running step key3'),
        call('step1 not running because run is False.'),
        call('foreach decorator looped 3 times.')]

    assert mock_invoke.call_count == 1

    # validate all the in params ended up in context as intended, plus i
    assert len(context) == original_len + 1
    # after the looping's done, the i value will be the last iterator value
    assert context['i'] == 'key3'
    assert step.for_counter == 'key3'


def mock_step_mutating_skip(context):
    """Mock a step's run_step by setting a context value False."""
    context['dynamic_skip_expression'] = True


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=mock_step_mutating_skip)
def test_foreach_evaluates_skip_decorator(mock_invoke, mock_moduleloader):
    """The foreach evaluates skip expression on each loop iteration."""
    step = Step({'name': 'step1',
                 'skip': '{dynamic_skip_expression}',
                 'foreach': ['{key1}', '{key2}', 'key3']})

    context = get_test_context()
    context['dynamic_skip_expression'] = False
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('foreach: running step value1'),
        call('foreach: running step value2'),
        call('step1 not running because skip is True.'),
        call('foreach: running step key3'),
        call('step1 not running because skip is True.'),
        call('foreach decorator looped 3 times.')]

    assert mock_invoke.call_count == 1

    # validate all the in params ended up in context as intended, plus i
    assert len(context) == original_len + 1
    # after the looping's done, the i value will be the last iterator value
    assert context['i'] == 'key3'
    assert step.for_counter == 'key3'


@patch('pypyr.moduleloader.get_module')
def test_foreach_evaluates_swallow_decorator(mock_moduleloader):
    """The foreach evaluates skip expression on each loop iteration."""
    step = Step({'name': 'step1',
                 'swallow': '{dynamic_swallow_expression}',
                 'foreach': ['{key1}', '{key2}', 'key3']})

    context = get_test_context()
    context['dynamic_swallow_expression'] = False
    original_len = len(context)

    arb_error = ValueError('arb error')

    def mock_step_deliberate_error(context):
        """Mock step's run_step by setting swallow False and raising err."""
        if context['i'] == 'value2':
            context['dynamic_swallow_expression'] = True
        elif context['i'] == 'key3':
            raise arb_error

    with patch.object(Step, 'invoke_step',
                      side_effect=mock_step_deliberate_error) as mock_invoke:
        with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
            with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
                step.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('foreach: running step value1'),
        call('foreach: running step value2'),
        call('foreach: running step key3'),
        call('foreach decorator looped 3 times.')]

    assert mock_invoke.call_count == 3

    assert mock_logger_error.call_count == 1
    mock_logger_error.assert_called_once_with(
        'step1 Ignoring error '
        'because swallow is True for this step.\nValueError: arb error')

    # validate all the in params ended up in context as intended, plus i,
    # plus runErrors
    assert len(context) == original_len + 2
    # after the looping's done, the i value will be the last iterator value
    assert context['i'] == 'key3'
    assert step.for_counter == 'key3'
    assert context['runErrors'] == [{
        'col': None,
        'customError': {},
        'description': 'arb error',
        'exception': arb_error,
        'line': None,
        'name': 'ValueError',
        'step': step.name,
        'swallowed': True,
    }]


def test_foreach_with_iterator():
    """Loop over iterator in foreach."""
    context = Context({'lst': []})
    from itertools import product
    context.pystring_globals_update({'product': product})

    step = Step({'name': 'pypyr.steps.py',
                 'foreach': PyString('product([1, 2], ["A", "B"])'),
                 'in': {'py': 'lst.append(i)'}
                 })

    step.run_step(context)

    assert context == {'lst': [(1, 'A'), (1, 'B'), (2, 'A'), (2, 'B')],
                       'i': (2, 'B')}


def test_foreach_with_inline_iterator():
    """Loop over iterator in foreach."""
    def myfunc():
        yield from ['one', 'two', 'three']

    context = Context({'lst': [],
                       'test_iterator': myfunc()})

    step = Step({'name': 'pypyr.steps.py',
                 'foreach': PyString('test_iterator'),
                 'in': {'py': 'lst.append(i)'}
                 })

    step.run_step(context)

    assert len(context) == 3
    assert context['lst'] == ['one', 'two', 'three']
    assert context['i'] == 'three'

# endregion Step: run_step

# region Step: run_step: while


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_while_max(mock_invoke, mock_moduleloader):
    """The while runs to max."""
    step = Step({'name': 'step1',
                 'while': {'max': 3}})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 3 times at 0.0s intervals.'),
        call('while: running step with counter 1'),
        call('while: running step with counter 2'),
        call('while: running step with counter 3')]

    assert mock_invoke.call_count == 3

    # validate all the in params ended up in context as intended, plus counter
    assert len(context) == original_len + 1
    # after the looping's done, the counter value will be the last iterator
    assert context['whileCounter'] == 3
    assert step.while_decorator.while_counter == 3


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=mock_step_mutating_run)
def test_while_evaluates_run_decorator(mock_invoke, mock_moduleloader):
    """The while evaluates run_me expression on each loop iteration."""
    step = Step({'name': 'step1',
                 'run': '{dynamic_run_expression}',
                 'while': {'max': '{whileMax}', 'stop': '{key5}'}})

    context = get_test_context()
    context['dynamic_run_expression'] = True
    context['whileMax'] = 3
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 3 times, or until {key5} evaluates to '
             'True at 0.0s intervals.'),
        call('while: running step with counter 1'),
        call('while: running step with counter 2'),
        call('step1 not running because run is False.'),
        call('while: running step with counter 3'),
        call('step1 not running because run is False.'),
        call('while decorator looped 3 times, and {key5} never evaluated to '
             'True.')]

    assert mock_invoke.call_count == 1

    # validate all the in params ended up in context as intended, plus i
    assert len(context) == original_len + 1
    # after the looping's done, the i value will be the last iterator value
    assert context['whileCounter'] == 3
    assert step.while_decorator.while_counter == 3


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=[None, ValueError('whoops')])
def test_while_error_kicks_loop(mock_invoke, mock_moduleloader):
    """Error during while kicks loop."""
    step = Step({'name': 'step1',
                 'while': {'max': 3}})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with pytest.raises(ValueError) as err_info:
            step.run_step(context)

    assert str(err_info.value) == "whoops"

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 3 times at 0.0s intervals.'),
        call('while: running step with counter 1'),
        call('while: running step with counter 2')]

    assert mock_invoke.call_count == 2

    # validate all the in params ended up in context as intended, plus i
    # plus runErrors
    assert len(context) == original_len + 2
    # after the looping's done, the counter will be the last iterator value
    assert context['whileCounter'] == 2
    assert step.while_decorator.while_counter == 2
    assert context['runErrors'] == [{
        'col': None,
        'customError': {},
        'description': 'whoops',
        'exception': err_info.value,
        'line': None,
        'name': 'ValueError',
        'step': step.name,
        'swallowed': False,
    }]


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_while_exhausts(mock_invoke, mock_moduleloader):
    """While exhausts throws error on errorOnMax."""
    step = Step({'name': 'step1',
                 'while': {'max': '{whileMax}',
                           'stop': '{key5}',
                           'errorOnMax': '{key6}'}})

    context = get_test_context()
    context['whileMax'] = 3
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with pytest.raises(LoopMaxExhaustedError) as err_info:
            step.run_step(context)

    assert str(err_info.value) == ("while loop reached "
                                   "3 and {key5} never evaluated to True.")

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 3 times, or until {key5} evaluates to '
             'True at 0.0s intervals.'),
        call('while: running step with counter 1'),
        call('while: running step with counter 2'),
        call('while: running step with counter 3')]

    assert mock_invoke.call_count == 3

    # validate all the in params ended up in context as intended, plus i
    assert len(context) == original_len + 1
    # after the looping's done, the i value will be the last iterator value
    assert context['whileCounter'] == 3
    assert step.while_decorator.while_counter == 3


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_while_exhausts_hard_true(mock_invoke, mock_moduleloader):
    """While evaluates run_me expression on each loop iteration, no format."""
    step = Step({'name': 'step1',
                 'while': {'max': '{whileMax}',
                           'stop': False,
                           'errorOnMax': True}})

    context = get_test_context()
    context['whileMax'] = 3
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with pytest.raises(LoopMaxExhaustedError) as err_info:
            step.run_step(context)

    assert str(err_info.value) == "while loop reached 3."

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 3 times, or until False evaluates to '
             'True at 0.0s intervals.'),
        call('while: running step with counter 1'),
        call('while: running step with counter 2'),
        call('while: running step with counter 3')]

    assert mock_invoke.call_count == 3

    # validate all the in params ended up in context as intended, plus i
    assert len(context) == original_len + 1
    # after the looping's done, the i value will be the last iterator value
    assert context['whileCounter'] == 3
    assert step.while_decorator.while_counter == 3


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'run_conditional_decorators')
@patch('unittest.mock.MagicMock', new=DeepCopyMagicMock)
def test_while_nests_foreach_with_substitutions(mock_run, mock_moduleloader):
    """While loops twice, foreach thrice with substitutions inside a list."""
    step = Step({'name': 'step1',
                 'foreach': ['{key1}', '{key2}', 'key3'],
                 'while': {'max': 2}
                 })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 2 times at 0.0s intervals.'),
        call('while: running step with counter 1'),
        call('foreach: running step value1'),
        call('foreach: running step value2'),
        call('foreach: running step key3'),
        call('foreach decorator looped 3 times.'),
        call('while: running step with counter 2'),
        call('foreach: running step value1'),
        call('foreach: running step value2'),
        call('foreach: running step key3'),
        call('foreach decorator looped 3 times.')]

    assert mock_run.call_count == 6
    mutated_context = get_test_context()
    mutated_context['whileCounter'] = 1
    mutated_context['i'] = 'value1'
    mock_run.assert_any_call(mutated_context)
    mutated_context['i'] = 'value2'
    mock_run.assert_any_call(mutated_context)
    mutated_context['i'] = 'key3'
    mock_run.assert_any_call(mutated_context)

    mutated_context['whileCounter'] = 2
    mutated_context['i'] = 'value1'
    mock_run.assert_any_call(mutated_context)
    mutated_context['i'] = 'value2'
    mock_run.assert_any_call(mutated_context)
    mutated_context['i'] = 'key3'
    mock_run.assert_any_call(mutated_context)

    # validate all the in params ended up in context as intended, plus i
    assert len(context) == original_len + 2
    # after the looping's done, the i value will be the last iterator value
    assert context['i'] == 'key3'
    assert step.for_counter == 'key3'
    assert context['whileCounter'] == 2
    assert step.while_decorator.while_counter == 2

# endregion Step: run_step: while

# region Step: invoke_step


@patch('pypyr.moduleloader.get_module')
def test_invoke_step_pass(mocked_moduleloader):
    """run_pipeline_step test pass."""
    stepcache.step_cache.clear()
    step = Step('mocked.step')
    step.invoke_step(get_test_context())

    mocked_moduleloader.assert_called_once_with('mocked.step')
    mocked_moduleloader.return_value.run_step.assert_called_once_with(
        {'key1': 'value1',
         'key2': 'value2',
         'key3': 'value3',
         'key4': [
             {'k4lk1': 'value4', 'k4lk2': 'value5'},
             {'k4lk1': 'value6', 'k4lk2': 'value7'}],
         'key5': False,
         'key6': True,
         'key7': 77})


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_invoke_step_context_abides(mocked_stepcache):
    """Step mutates context & mutation abides after run_pipeline_step."""
    mocked_stepcache.return_value = mock_run_step
    context = get_test_context()

    step = Step('mocked.step')
    step.invoke_step(context)

    mocked_stepcache.assert_called_once_with('mocked.step')
    assert context['test_run_step'] == 'this was set in step'


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_invoke_step_empty_context(mocked_stepcache):
    """Empty context in step (i.e count == 0, but not is None)."""
    mocked_stepcache.return_value = mock_run_step_empty_context
    context = get_test_context()

    step = Step('mocked.step')
    step.invoke_step(context)

    mocked_stepcache.assert_called_once_with('mocked.step')
    assert len(context) == 0
    assert context is not None


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_invoke_step_none_context(mocked_stepcache):
    """Step rebinding context to None doesn't affect the caller Context."""
    mocked_stepcache.return_value = mock_run_step_none_context
    context = get_test_context()

    step = Step('mocked.step')
    step.invoke_step(False)

    mocked_stepcache.assert_called_once_with('mocked.step')
    assert context == {'key1': 'value1',
                       'key2': 'value2',
                       'key3': 'value3',
                       'key4': [
                           {'k4lk1': 'value4', 'k4lk2': 'value5'},
                           {'k4lk1': 'value6', 'k4lk2': 'value7'}],
                       'key5': False,
                       'key6': True,
                       'key7': 77}

# endregion Step: invoke_step

# region Step: reset_context_counters


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_reset_context_counters(mock_step_cache):
    """Reset all counters in context."""
    context = {'a': 'b',
               'c': 'd',
               'whileCounter': 99,
               'retryCounter': 999,
               'i': '9999'}

    call = Call(['one', 'two'], 'sg', 'fg', ('a', 'changed'))

    step_config = {'name': 'blah',
                   'while': {
                       'max': 4
                   },
                   'foreach': ['one', 'two'],
                   'retry': {
                       'max': 5
                   }
                   }

    step = Step(step_config)
    step.while_decorator.while_counter = 6
    step.for_counter = 'seven'
    step.retry_decorator.retry_counter = 8

    step.reset_context_counters(context, call)

    assert context == {'a': 'changed',
                       'c': 'd',
                       'whileCounter': 6,
                       'i': 'seven',
                       'retryCounter': 8}


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_reset_context_counters_dont_need_updating(mock_step_cache):
    """Reset all counters in context when they don't need to update."""
    context = {'a': 'b',
               'c': 'd',
               'whileCounter': 99,
               'retryCounter': 999,
               'i': '9999'}

    call = Call(['one', 'two'], 'sg', 'fg', ('a', 'b'))

    step_config = {'name': 'blah',
                   'while': {
                       'max': 4
                   },
                   'foreach': ['one', 'two'],
                   'retry': {
                       'max': 5
                   }
                   }

    step = Step(step_config)
    step.while_decorator.while_counter = 99
    step.for_counter = '9999'
    step.retry_decorator.retry_counter = 999

    step.reset_context_counters(context, call)

    assert context == {'a': 'b',
                       'c': 'd',
                       'whileCounter': 99,
                       'i': '9999',
                       'retryCounter': 999}


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_reset_context_counters_none(mock_step_cache):
    """Reset but no counters available & key not found in context."""
    context = {'a': 'b',
               'c': 'd'}

    call = Call(['one', 'two'], 'sg', 'fg', ('x', 'z'))

    step_config = {'name': 'blah'}

    step = Step(step_config)

    step.reset_context_counters(context, call)

    # reset added the key that didn't exist to context
    assert context == {'a': 'b',
                       'c': 'd',
                       'x': 'z'}


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_reset_context_counters_none_none(mock_step_cache):
    """Reset key to none should not be possible."""
    context = {'a': 'b',
               'c': 'd'}

    call = Call(['one', 'two'], 'sg', 'fg', ('x', None))

    step_config = {'name': 'blah'}

    step = Step(step_config)

    with pytest.raises(AssertionError):
        step.reset_context_counters(context, call)


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_reset_context_counters_mutable(mock_step_cache):
    """Reset to a mutable object."""
    arb_mutable = ['b']
    context = {'a': arb_mutable,
               'c': 'd'}

    call = Call(['one', 'two'], 'sg', 'fg', ('a', arb_mutable))

    step_config = {'name': 'blah'}

    step = Step(step_config)

    step.reset_context_counters(context, call)

    assert context == {'a': ['b'],
                       'c': 'd'}


@patch('pypyr.cache.stepcache.step_cache.get_step')
def test_reset_context_counters_mutate(mock_step_cache):
    """Reset to a mutating mutable."""
    arb_mutable = ['b']
    context = {'a': arb_mutable,
               'c': 'd'}

    call = Call(['one', 'two'], 'sg', 'fg', ('a', arb_mutable))

    step_config = {'name': 'blah'}

    step = Step(step_config)

    arb_mutable[0] = 'changed'

    step.reset_context_counters(context, call)

    assert context == {'a': ['changed'],
                       'c': 'd'}
# endregion Step: reset_context_counters

# region Step: run_step: run


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_true(mock_invoke_step,
                                                  mock_get_module):
    """Complex step with run decorator set true will run step."""
    step = Step({'name': 'step1',
                 'run': True})

    context = get_test_context()
    original_len = len(context)

    step.run_step(context)

    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_false(mock_invoke_step,
                                                   mock_get_module):
    """Complex step with run decorator set false doesn't run step."""
    step = Step({'name': 'step1',
                 'run': False})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call("step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_str_formatting_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with run formatting expression false doesn't run step."""
    step = Step({
        'name': 'step1',
        # name will evaluate False because it's a string and it's not 'True'.
        'run': '{key1}'})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call("step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_str_false(mock_invoke_step,
                                                       mock_get_module):
    """Complex step with run set to string False doesn't run step."""
    step = Step({
        'name': 'step1',
        # name will evaluate False because it's a string and it's not 'True'.
        'run': 'False'})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_str_lower_false(mock_invoke_step,
                                                             mock_get_module):
    """Complex step with run set to string false doesn't run step."""
    step = Step({
        'name': 'step1',
        # name will evaluate False because it's a string and it's not 'True'.
        'run': 'false'})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_bool_formatting_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with run formatting expression false doesn't run step."""
    step = Step({
        'name': 'step1',
                # key5 will evaluate False because it's a bool and it's False
                'run': '{key5}'})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_bool_formatting_true(
        mock_invoke_step,
        mock_get_module):
    """Complex step with run formatting expression true runs step."""
    step = Step({
        'name': 'step1',
        # key6 will evaluate True because it's a bool and it's True
        'run': '{key6}'})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_string_true(mock_invoke_step,
                                                         mock_get_module):
    """Complex step with run formatting expression True runs step."""
    step = Step({
        'name': 'step1',
        # 'True' will evaluate bool True
        'run': 'True'})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_1_true(mock_invoke_step,
                                                    mock_get_module):
    """Complex step with run 1 runs step."""
    step = Step({
        'name': 'step1',
        # 1 will evaluate True because it's an int and 1
        'run': 1})

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_99_true(mock_invoke_step,
                                                     mock_get_module):
    """Complex step with run 99 runs step."""
    step = Step({
        'name': 'step1',
        # 99 will evaluate True because it's an int and > 0
        'run': 99
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_neg1_true(mock_invoke_step,
                                                       mock_get_module):
    """Complex step with run -1 runs step."""
    step = Step({
        'name': 'step1',
        # -1 will evaluate True because it's an int and != 0
        'run': -1
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_with_single_retry(mock_invoke_step,
                                              mock_get_module):
    """Complex step with retry runs step."""
    step = Step({
        'name': 'step1',
        # -1 will evaluate True because it's an int and != 0
        'retry': {'max': 10}
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        {'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
         'key5': False,
         'key6': True,
         'key7': 77,
         'retryCounter': 1})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len + 1
    assert context['retryCounter'] == 1


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_with_retries(mock_invoke_step,
                                         mock_get_module):
    """Complex step with retry runs step."""
    step = Step({
        'name': 'step1',
        # -1 will evaluate True because it's an int and != 0
        'retry': {'max': 0}
    })

    context = get_test_context()
    original_len = len(context)

    mock_invoke_step.side_effect = [ValueError('arb'), None]

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    assert mock_invoke_step.call_count == 2
    mock_invoke_step.assert_called_with(
        {'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
         'key5': False,
         'key6': True,
         'key7': 77,
         'retryCounter': 2})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len + 1


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=ValueError('arb error here'))
def test_run_on_error(mock_invoke_step,
                      mock_get_module):
    """Complex step with swallow false raises error."""
    complex_step_info = CommentedMap({
        'name': 'step1',
        'swallow': 0,
        'onError': {'arb': 'value'}
    })

    complex_step_info._yaml_set_line_col(5, 6)

    step = Step(complex_step_info)

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        with pytest.raises(ValueError) as err_info:
            step.run_step(context)

            assert str(err_info.value) == "arb error here"

    mock_logger_error.assert_called_once_with(
        "Error while running step step1 at pipeline yaml line: 6, col: 7")

    # validate all the in params ended up in context as intended,
    # plus runErrors
    assert len(context) == original_len + 1
    assert context['runErrors'] == [{
        'col': 7,
        'customError': {'arb': 'value'},
        'description': 'arb error here',
        'exception': err_info.value,
        'line': 6,
        'name': 'ValueError',
        'step': step.name,
        'swallowed': False,
    }]
# endregion Step: run_step: run


# region Step: run_step: skip
@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_false(mock_invoke_step,
                                                    mock_get_module):
    """Complex step with skip decorator set false will run step."""
    step = Step({
        'name': 'step1',
        'skip': False
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_true(mock_invoke_step,
                                                   mock_get_module):
    """Complex step with skip decorator set true runa step."""
    step = Step({
        'name': 'step1',
        'skip': True
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
@pytest.mark.parametrize("description", [None, "arb description"])
def test_run_pipeline_steps_run_false_with_skip_invalid(mock_invoke_step,
                                                        mock_get_module,
                                                        description):
    """Skip is not called if run is False."""
    step = Step(
        {
            'name': 'step1',
            'run': False,
            'description': description,
            'skip': PyString("invalid")
        })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_str_formatting_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with skip formatting expression false doesn't run step."""
    step = Step({
        'name': 'step1',
        # name will evaluate True
        'skip': '{key6}'
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_str_true(mock_invoke_step,
                                                       mock_get_module):
    """Complex step with skip set to string False doesn't run step."""
    step = Step({
        'name': 'step1',
        # skip evaluates True because it's a string and TRUE parses to True.
        'skip': 'TRUE'
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_str_lower_true(mock_invoke_step,
                                                             mock_get_module):
    """Complex step with run set to string true doesn't run step."""
    step = Step({
        'name': 'step1',
        # skip will evaluate true because it's a string and true is True.
        'skip': 'true'
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_run_and_skip_bool_formatting_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with run doesn't run step, evals before skip."""
    step = Step({
        'name': 'step1',
        # key5 will evaluate False because it's a bool and it's False
        'run': '{key5}',
        'skip': True
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because run is False.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_bool_formatting_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with skip formatting expression true runs step."""
    step = Step({
        'name': 'step1',
        # key5 will evaluate False because it's a bool and it's False
        'skip': '{key5}'
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_string_false(
        mock_invoke_step,
        mock_get_module):
    """Complex step with skip formatting expression False runs step."""
    step = Step({
        'name': 'step1',
        # 'False' will evaluate bool False
        'skip': 'False'
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_0_true(
        mock_invoke_step,
        mock_get_module):
    """Complex step with run 1 runs step."""
    step = Step({
        'name': 'step1',
        # 0 will evaluate False because it's an int and 0
        'skip': 0
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_99_true(
        mock_invoke_step,
        mock_get_module):
    """Complex step with skip 99 doesn't run step."""
    step = Step({
        'name': 'step1',
        # 99 will evaluate True because it's an int and > 0
        'skip': 99
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call(
        "step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_with_skip_neg1_true(mock_invoke_step,
                                                        mock_get_module):
    """Complex step with run -1 runs step."""
    step = Step({
        'name': 'step1',
        # -1 will evaluate True because it's an int and != 0
        'skip': -1
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        step.run_step(context)

    mock_logger_info.assert_any_call("step1 not running because skip is True.")
    mock_invoke_step.assert_not_called()

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


# endregion Step: run_step: skip

# region Step: run_step: swallow
@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_swallow_true(mock_invoke_step,
                                                 mock_get_module):
    """Complex step with swallow true runs normally even without error."""
    step = Step({
        'name': 'step1',
        'swallow': True
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_swallow_false(mock_invoke_step,
                                                  mock_get_module):
    """Complex step with swallow false runs normally even without error."""
    step = Step({
        'name': 'step1',
        'swallow': False
    })

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch('unittest.mock.MagicMock', new=DeepCopyMagicMock)
def test_run_pipeline_steps_complex_swallow_true_error(mock_get_module):
    """Complex step with swallow true swallows error."""
    step = Step({
        'name': 'step1',
        'swallow': 1
    })

    context = get_test_context()
    original_len = len(context)

    arb_error = ValueError('arb error here')
    with patch.object(
            Step, 'invoke_step', side_effect=arb_error) as mock_invoke_step:
        with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
            with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
                step.run_step(context)

    mock_logger_debug.assert_any_call("done")
    mock_logger_error.assert_called_once_with(
        "step1 Ignoring error because swallow is True "
        "for this step.\n"
        "ValueError: arb error here")
    mock_invoke_step.assert_called_once_with(
        context={'key1': 'value1',
                 'key2': 'value2',
                 'key3': 'value3',
                 'key4': [
                     {'k4lk1': 'value4',
                      'k4lk2': 'value5'},
                     {'k4lk1': 'value6',
                      'k4lk2': 'value7'}
                 ],
                 'key5': False,
                 'key6': True,
                 'key7': 77})

    # validate all the in params ended up in context as intended,
    # plus runErrors
    assert len(context) == original_len + 1
    assert context['runErrors'] == [{
        'col': None,
        'customError': {},
        'description': 'arb error here',
        'exception': arb_error,
        'line': None,
        'name': 'ValueError',
        'step': step.name,
        'swallowed': True,
    }]


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
def test_run_pipeline_steps_complex_swallow_invalid_error(mock_invoke_step,
                                                          mock_get_module):
    """Complex step with swallow raising formatter error."""
    err = ValueError('arb error here')
    mock_invoke_step.side_effect = err

    step = Step({
        'name': 'step1',
        'swallow': PyString("invalid")
    })

    context = get_test_context()
    original_len = len(context)

    with pytest.raises(NameError) as err_info:
        step.run_step(context)

    mock_invoke_step.assert_called_once()
    assert str(err_info.value) == "name 'invalid' is not defined"

    # validate all the in params ended up in context as intended,
    assert len(context) == original_len


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=ValueError('arb error here'))
def test_run_pipeline_steps_complex_swallow_false_error(mock_invoke_step,
                                                        mock_get_module):
    """Complex step with swallow false raises error."""
    step = Step({
        'name': 'step1',
        'swallow': 0
    })

    context = get_test_context()
    original_len = len(context)

    with pytest.raises(ValueError) as err_info:
        step.run_step(context)

    assert str(err_info.value) == "arb error here"

    # validate all the in params ended up in context as intended,
    # plus runErrors
    assert len(context) == original_len + 1
    assert context['runErrors'] == [{
        'col': None,
        'customError': {},
        'description': 'arb error here',
        'exception': err_info.value,
        'line': None,
        'name': 'ValueError',
        'step': step.name,
        'swallowed': False,
    }]


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=ValueError('arb error here'))
def test_run_pipeline_steps_complex_round_trip(mock_invoke_step,
                                               mock_get_module):
    """Complex step with swallow false raises error."""
    complex_step_info = CommentedMap({
        'name': 'step1',
        'swallow': 0
    })

    complex_step_info._yaml_set_line_col(5, 6)

    step = Step(complex_step_info)

    context = get_test_context()
    original_len = len(context)

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        with pytest.raises(ValueError) as err_info:
            step.run_step(context)

            assert str(err_info.value) == "arb error here"

    mock_logger_error.assert_called_once_with(
        "Error while running step step1 at pipeline yaml line: 6, col: 7")

    # validate all the in params ended up in context as intended,
    # plus runErrors
    assert len(context) == original_len + 1
    assert context['runErrors'] == [{
        'col': 7,
        'customError': {},
        'description': 'arb error here',
        'exception': err_info.value,
        'line': 6,
        'name': 'ValueError',
        'step': step.name,
        'swallowed': False,
    }]


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=ValueError('arb error here'))
def test_run_pipeline_steps_complex_swallow_defaults_false_error(
        mock_invoke_step,
        mock_get_module):
    """Complex step with swallow not specified still raises error."""
    step = Step({
        'name': 'step1'
    })

    context = get_test_context()
    original_len = len(context)

    with pytest.raises(ValueError) as err_info:
        step.run_step(context)

    assert str(err_info.value) == "arb error here"

    # validate all the in params ended up in context as intended,
    # plus runErrors
    assert len(context) == original_len + 1
    assert context['runErrors'] == [{
        'col': None,
        'customError': {},
        'description': 'arb error here',
        'exception': err_info.value,
        'line': None,
        'name': 'ValueError',
        'step': step.name,
        'swallowed': False,
    }]


@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step', side_effect=ValueError('arb error here'))
@patch('unittest.mock.MagicMock', new=DeepCopyMagicMock)
def test_run_pipeline_steps_simple_with_error(mock_invoke_step,
                                              mock_get_module):
    """Simple step run with error should not swallow."""
    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        step = Step('step1')
        with pytest.raises(ValueError) as err_info:
            step.run_step(Context({'k1': 'v1'}))

            assert str(err_info.value) == "arb error here"

    mock_logger_debug.assert_any_call('step1 is a simple string.')
    mock_invoke_step.assert_called_once_with(
        context={'k1': 'v1'})

# endregion Step: run_step: swallow


# region Step: run_step: input context

@patch('pypyr.moduleloader.get_module')
@patch.object(Step, 'invoke_step')
@patch('unittest.mock.MagicMock', new=DeepCopyMagicMock)
def test_run_step_in_with_clean(mock_invoke_step, mock_get_module):
    """Step sets 'in' arguments in context, unset from context when done."""
    step = Step({
        'name': 'step1',
        'in': {
            'key1': 'updated1',
            'key2': 'updated2',
            'keyadded': 'added3'
        }
    })

    context = get_test_context()
    step.run_step(context)

    # step called with context updated with 'in' arguments
    assert mock_invoke_step.call_count == 1
    assert mock_invoke_step.call_args_list[0] == call(context={
        'key1': 'updated1',
        'key2': 'updated2',
        'key3': 'value3',
        'key4': [
                {'k4lk1': 'value4',
                 'k4lk2': 'value5'},
                {'k4lk1': 'value6',
                 'k4lk2': 'value7'}
        ],
        'key5': False,
        'key6': True,
        'key7': 77,
        'keyadded': 'added3'})

    # context when done has 'in' args removed.
    assert context == {'key3': 'value3',
                       'key4': [
                           {'k4lk1': 'value4',
                            'k4lk2': 'value5'},
                           {'k4lk1': 'value6',
                            'k4lk2': 'value7'}
                       ],
                       'key5': False,
                       'key6': True,
                       'key7': 77}

# endregion Step: run_step: input context

# region Step: set_step_input_context


@patch('pypyr.moduleloader.get_module')
def test_set_step_input_context_no_in_simple(mocked_moduleloader):
    """Set step context does nothing if no in key found in simple step."""
    step = Step('blah')
    context = get_test_context()
    step.set_step_input_context(context)

    assert context == get_test_context()


@patch('pypyr.moduleloader.get_module')
def test_set_step_input_context_no_in_complex(mocked_moduleloader):
    """Set step context does nothing if no in key found in complex step."""
    step = Step({'name': 'blah'})
    context = get_test_context()
    step.set_step_input_context(context)

    assert context == get_test_context()


@patch('pypyr.moduleloader.get_module')
def test_set_step_input_context_in_empty(mocked_moduleloader):
    """Set step context does nothing if in key found but it's empty."""
    step = Step({'name': 'blah', 'in': {}})
    context = get_test_context()
    step.set_step_input_context(context)

    assert context == get_test_context()


@patch('pypyr.moduleloader.get_module')
def test_set_step_input_context_with_in(mocked_moduleloader):
    """Set step context adds in to context."""
    context = get_test_context()
    original_len = len(context)
    in_args = {'newkey1': 'v1',
               'newkey2': 'v2',
               'key3': 'updated in',
               'key4': [0, 1, 2, 3],
               'key5': True,
               'key6': False,
               'key7': 88}
    step = Step({'name': 'blah', 'in': in_args})
    step.set_step_input_context(context)

    assert len(context) - 2 == original_len
    assert context['newkey1'] == 'v1'
    assert context['newkey2'] == 'v2'
    assert context['key1'] == 'value1'
    assert context['key2'] == 'value2'
    assert context['key3'] == 'updated in'
    assert context['key4'] == [0, 1, 2, 3]
    assert context['key5']
    assert not context['key6']
    assert context['key7'] == 88

# endregion Step: set_step_input_context

# region Step: unset_step_input_context


def test_unset_step_input_context_in_none():
    """Unset works when in parameters None."""
    context = get_test_context()
    step = Step({'name': 'blah', 'in': None})
    step.unset_step_input_context(context)

    # Nothing removed because 'in' was None
    assert context == get_test_context()


def test_unset_step_input_context_in_empty():
    """Unset works when in parameters exists but is empty."""
    context = get_test_context()
    step = Step({'name': 'blah', 'in': {}})
    step.unset_step_input_context(context)

    # Nothing removed because 'in' was empty list
    assert context == get_test_context()


def test_unset_step_input_context():
    """Unset works when in parameters specified."""
    context = get_test_context()
    in_args = {'newkey1': 'v1',
               'newkey2': 'v2',
               'key3': 'updated in',
               'key4': [0, 1, 2, 3],
               'key5': True,
               'key6': False,
               'key7': 88}
    step = Step({'name': 'blah', 'in': in_args})
    step.unset_step_input_context(context)

    # Removed existing keys & non-existing keys specified in 'in' from context
    assert context == {'key1': 'value1',
                       'key2': 'value2'}

# endregion Step: unset_step_input_context


# region Step: save_error
@patch('pypyr.moduleloader.get_module')
def test_save_error_with_no_previous_errors_in_context(mocked_moduleloader):
    """Save error."""
    step = Step({'name': 'blah'})
    context = get_test_context()
    original_len = len(context)
    arb_error = ValueError("arb error")
    step.save_error(context, exception=arb_error, swallowed=False)

    assert len(context) == original_len + 1

    # validate all except runErrors
    assert get_test_context().items() <= context.items()

    assert context['runErrors'] == [{
        'col': None,
        'customError': {},
        'description': 'arb error',
        'exception': arb_error,
        'line': None,
        'name': 'ValueError',
        'step': step.name,
        'swallowed': False,
    }]


@patch('pypyr.moduleloader.get_module')
def test_save_error_round_trip(mocked_moduleloader):
    """Save error with CommentedMap."""
    context = get_test_context()
    step_info = CommentedMap({'name': 'arb step'})
    step_info._yaml_set_line_col(6, 7)
    step = Step(step_info)
    original_len = len(context)
    arb_error = ValueError("arb error")
    step.save_error(context, exception=arb_error, swallowed=True)

    assert len(context) == original_len + 1
    assert get_test_context().items() <= context.items()

    assert context['runErrors'] == [{
        'col': 8,
        'customError': {},
        'description': 'arb error',
        'exception': arb_error,
        'line': 7,
        'name': 'ValueError',
        'step': step.name,
        'swallowed': True,
    }]


@patch('pypyr.moduleloader.get_module')
def test_save_error_formatted(mocked_moduleloader):
    """Save error with formatting expression."""
    step = Step({'name': 'blah', 'onError': {'key': '{key1}'}})
    context = get_test_context()
    original_len = len(context)
    arb_error = ValueError("arb error")
    step.save_error(context, exception=arb_error, swallowed=False)

    assert len(context) == original_len + 1
    assert get_test_context().items() <= context.items()

    assert context['runErrors'] == [{
        'col': None,
        'customError': {'key': 'value1'},
        'description': 'arb error',
        'exception': arb_error,
        'line': None,
        'name': 'ValueError',
        'step': step.name,
        'swallowed': False,
    }]


@patch('pypyr.moduleloader.get_module')
def test_save_error_multiple_call(mocked_moduleloader):
    """Save multiple errors."""
    step = Step({'name': 'blah'})
    context = get_test_context()
    original_len = len(context)

    first_arb_error = ValueError("arb error first")
    step.save_error(context, exception=first_arb_error, swallowed=True)

    second_arb_error = RuntimeError("arb error second")
    step.save_error(context, exception=second_arb_error, swallowed=False)

    assert len(context) == original_len + 1
    assert get_test_context().items() <= context.items()

    assert len(context['runErrors']) == 2

    assert context['runErrors'][0] == {
        'col': None,
        'customError': {},
        'description': 'arb error first',
        'exception': first_arb_error,
        'line': None,
        'name': 'ValueError',
        'step': step.name,
        'swallowed': True,
    }

    assert context['runErrors'][1] == {
        'col': None,
        'customError': {},
        'description': 'arb error second',
        'exception': second_arb_error,
        'line': None,
        'name': 'RuntimeError',
        'step': step.name,
        'swallowed': False,
    }

# endregion Step: save_error
# endregion Step

# region RetryDecorator
# region RetryDecorator: init


def test_retry_init_defaults_all():
    """The RetryDecorator ctor sets defaults with nothing set."""
    rd = RetryDecorator({})
    assert rd.backoff is None
    assert rd.backoff_args is None
    assert rd.jrc == 0
    assert rd.max is None
    assert rd.sleep_max is None
    assert rd.sleep == 0
    assert rd.stop_on is None
    assert rd.retry_on is None
    assert rd.retry_counter is None


def test_retry_init_defaults_max():
    """The RetryDecorator ctor sets defaults with only max set."""
    rd = RetryDecorator({'max': 3})
    assert rd.backoff is None
    assert rd.backoff_args is None
    assert rd.jrc == 0
    assert rd.max == 3
    assert rd.sleep_max is None
    assert rd.sleep == 0
    assert rd.stop_on is None
    assert rd.retry_on is None
    assert rd.retry_counter is None


def test_retry_init_all_attributes():
    """The RetryDecorator ctor with all props set."""
    rd = RetryDecorator({'max': 3,
                         'sleep': 4.4,
                         'retryOn': [1, 2, 3],
                         'stopOn': [4, 5, 6],
                         'backoff': 'arb',
                         'sleepMax': 5.5,
                         'jrc': 6.6,
                         'backoffArgs': {'a': 'b'}}
                        )
    assert rd.backoff == 'arb'
    assert rd.backoff_args == {'a': 'b'}
    assert rd.jrc == 6.6
    assert rd.max == 3
    assert rd.sleep_max == 5.5
    assert rd.sleep == 4.4
    assert rd.stop_on == [4, 5, 6]
    assert rd.retry_on == [1, 2, 3]
    assert rd.retry_counter is None


def test_retry_init_not_a_dict():
    """The RetryDecorator raises PipelineDefinitionError on bad ctor input."""
    with pytest.raises(PipelineDefinitionError) as err_info:
        RetryDecorator('arb')

    assert str(err_info.value) == (
        "retry decorator must be a dict (i.e a map) type.")

# endregion RetryDecorator: init
# region RetryDecorator: exec_iteration


def test_retry_exec_iteration_returns_true_on_success():
    """exec_iteration returns True when no error on step method."""
    rd = RetryDecorator({'max': 3})

    context = Context({})
    mock = MagicMock()

    assert rd.exec_iteration(2, context, mock, 3)

    # context endures
    assert context['retryCounter'] == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 2})
    assert rd.retry_counter == 2


def test_retry_exec_iteration_returns_true_on_max_success():
    """exec_iteration returns True when no error on step method on max."""
    rd = RetryDecorator({'max': 3})

    context = Context({})
    mock = MagicMock()
    assert rd.exec_iteration(3, context, mock, 3)
    # context endures
    assert context['retryCounter'] == 3
    assert rd.retry_counter == 3
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 3})


def test_retry_exec_iteration_returns_false_on_error():
    """exec_iteration returns True when no error on step method."""
    rd = RetryDecorator({'max': 3})

    context = Context({})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        assert not rd.exec_iteration(2, context, mock, 3)
    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 2})
    mock_logger_error.assert_called_once_with('retry: ignoring error because '
                                              'retryCounter < max.\n'
                                              'ValueError: arb')


def test_retry_exec_iteration_returns_false_on_error_with_retryon():
    """exec_iteration returns False when error specified in retryOn."""
    rd = RetryDecorator({'max': 3,
                         'retryOn': ['KeyError', 'ValueError']})

    context = Context({})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        assert not rd.exec_iteration(2, context, mock, 3)
    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 2})
    mock_logger_error.assert_called_once_with('retry: ignoring error because '
                                              'retryCounter < max.\n'
                                              'ValueError: arb')


def test_retry_exec_iteration_returns_false_on_error_with_retryon_format():
    """exec_iteration returns False when error in retryOn with format."""
    rd = RetryDecorator({'max': 3,
                         'retryOn': ['KeyError', '{k1}']})

    context = Context({'k1': 'ValueError'})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
            assert not rd.exec_iteration(2, context, mock, 3)

    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 2
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'k1': 'ValueError', 'retryCounter': 2})
    mock_logger_error.assert_called_once_with('retry: ignoring error because '
                                              'retryCounter < max.\n'
                                              'ValueError: arb')
    mock_logger_debug.assert_any_call('ValueError in retryOn. Retry again.')


def test_retry_exec_iteration_raises_on_error_not_in_retryon():
    """exec_iteration raises when error not in retryOn."""
    rd = RetryDecorator({'max': 3,
                         'retryOn': ['KeyError', 'BlahError']})

    context = Context({})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        with pytest.raises(ValueError) as err_info:
            rd.exec_iteration(2, context, mock, 3)

        assert str(err_info.value) == 'arb'

    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 2})
    mock_logger_error.assert_called_once_with(
        'ValueError not in retryOn. Raising error and exiting retry.')


def test_retry_exec_iteration_raises_on_error_in_stopon():
    """exec_iteration raises when error in stopOn."""
    rd = RetryDecorator({'max': 3,
                         'stopOn': ['KeyError', 'ValueError']})

    context = Context({})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        with pytest.raises(ValueError) as err_info:
            rd.exec_iteration(2, context, mock, 3)

        assert str(err_info.value) == 'arb'

    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 2})
    mock_logger_error.assert_called_once_with(
        'ValueError in stopOn. Raising error and exiting retry.')


def test_retry_exec_iteration_raises_on_error_in_stopon_format():
    """exec_iteration raises when error in stopOn with formatting."""
    rd = RetryDecorator({'max': 3,
                         'stopOn': '{k1}'})

    context = Context({'k1': ['KeyError', 'ValueError']})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        with pytest.raises(ValueError) as err_info:
            rd.exec_iteration(2, context, mock, 3)

        assert str(err_info.value) == 'arb'

    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 2
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'k1': ['KeyError', 'ValueError'],
                                  'retryCounter': 2})
    mock_logger_error.assert_called_once_with(
        'ValueError in stopOn. Raising error and exiting retry.')


def test_retry_exec_iteration_returns_false_on_error_not_in_stopon():
    """exec_iteration returns False when error specified in stopOn."""
    rd = RetryDecorator({'max': 3,
                         'stopOn': ['KeyError', 'ArbError']})

    context = Context({})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        assert not rd.exec_iteration(2, context, mock, 3)
    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 2})
    mock_logger_error.assert_called_once_with('retry: ignoring error because '
                                              'retryCounter < max.\n'
                                              'ValueError: arb')


def test_retry_exec_iteration_returns_false_on_error_not_in_stopon_format():
    """exec_iteration returns False when error specified in stopOn."""
    rd = RetryDecorator({'max': 3,
                         'stopOn': '{k1}'})

    context = Context({'k1': ['KeyError', 'ArbError']})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
            assert not rd.exec_iteration(2, context, mock, 3)
    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 2
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'k1': ['KeyError', 'ArbError'],
                                  'retryCounter': 2})
    mock_logger_error.assert_called_once_with('retry: ignoring error because '
                                              'retryCounter < max.\n'
                                              'ValueError: arb')
    mock_logger_debug.assert_any_call('ValueError not in stopOn. Continue.')


def test_retry_exec_iteration_raises_on_error_in_stopon_with_retryon():
    """exec_iteration stopOn supersedes retryOn."""
    rd = RetryDecorator({'max': 3,
                         'stopOn': ['KeyError', 'ValueError'],
                         'retryOn': ['KeyError', 'ValueError']})

    context = Context({})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        with pytest.raises(ValueError) as err_info:
            rd.exec_iteration(2, context, mock, 3)

        assert str(err_info.value) == 'arb'

    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 2})
    mock_logger_error.assert_called_once_with(
        'ValueError in stopOn. Raising error and exiting retry.')


def test_retry_exec_iteration_raises_on_max_exhaust():
    """exec_iteration raises error if counter is max."""
    rd = RetryDecorator({'max': 3})

    context = Context({})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        with pytest.raises(ValueError) as err_info:
            rd.exec_iteration(3, context, mock, 3)

        assert str(err_info.value) == 'arb'

    # context endures
    assert context['retryCounter'] == 3
    assert rd.retry_counter == 3
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 3})
    mock_logger_debug.assert_called_with('retry: max 3 retries '
                                         'exhausted. raising error.')


def test_retry_exec_iteration_raises_on_max_exhaust_with_retryon():
    """exec_iteration raises error if counter is max and supersedes retryOn."""
    rd = RetryDecorator({'max': 3,
                         'retryOn': ['KeyError', 'ValueError']})

    context = Context({})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
        with pytest.raises(ValueError) as err_info:
            rd.exec_iteration(3, context, mock, 3)

        assert str(err_info.value) == 'arb'

    # context endures
    assert context['retryCounter'] == 3
    assert rd.retry_counter == 3
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 3})
    mock_logger_debug.assert_called_with('retry: max 3 retries '
                                         'exhausted. raising error.')


def test_retry_exec_iteration_handlederror():
    """Use inner exception when error type is HandledError."""
    rd = RetryDecorator({'max': 3,
                         'stopOn': ['KeyError', 'ArbError']})

    context = Context({})
    mock = MagicMock()
    err = HandledError()
    err.__cause__ = ValueError('arb')
    mock.side_effect = err

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        assert not rd.exec_iteration(2, context, mock, 3)
    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 2})
    mock_logger_error.assert_called_once_with('retry: ignoring error because '
                                              'retryCounter < max.\n'
                                              'ValueError: arb')


def test_retry_exec_iteration_handlederror_with_stopon():
    """exec_iteration evals inner error against stopon list."""
    rd = RetryDecorator({'max': 3,
                         'stopOn': '{k1}'})

    context = Context({'k1': ['KeyError', 'ArbError']})
    mock = MagicMock()
    err = HandledError()
    err.__cause__ = ValueError('arb')
    mock.side_effect = err

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
            assert not rd.exec_iteration(2, context, mock, 3)
    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 2
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'k1': ['KeyError', 'ArbError'],
                                  'retryCounter': 2})
    mock_logger_error.assert_called_once_with('retry: ignoring error because '
                                              'retryCounter < max.\n'
                                              'ValueError: arb')
    mock_logger_debug.assert_any_call('ValueError not in stopOn. Continue.')


def test_retry_exec_iteration_handlederror_stopon_raises():
    """exec_iteration raises HandledError on stopOn."""
    rd = RetryDecorator({'max': 3,
                         'stopOn': ['ValueError']})

    context = Context({})
    mock = MagicMock()
    err = HandledError()
    err.__cause__ = ValueError('arb')
    mock.side_effect = err

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        with pytest.raises(HandledError) as err_info:
            rd.exec_iteration(2, context, mock, 3)

        assert isinstance(err_info.value.__cause__, ValueError)
        assert str(err_info.value.__cause__) == 'arb'

    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 2})
    mock_logger_error.assert_called_once_with(
        'ValueError in stopOn. Raising error and exiting retry.')


def test_retry_exec_iteration_handlederror_retryon_raises():
    """exec_iteration raises HandledError on retryOn."""
    rd = RetryDecorator({'max': 3,
                         'retryOn': ['KeyError', 'BlahError']})

    context = Context({})
    mock = MagicMock()
    err = HandledError()
    err.__cause__ = ValueError('arb')
    mock.side_effect = err

    with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
        with pytest.raises(HandledError) as err_info:
            rd.exec_iteration(2, context, mock, 3)

        assert isinstance(err_info.value.__cause__, ValueError)
        assert str(err_info.value.__cause__) == 'arb'

    # context endures
    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'retryCounter': 2})
    mock_logger_error.assert_called_once_with(
        'ValueError not in retryOn. Raising error and exiting retry.')

# endregion RetryDecorator: exec_iteration


# region RetryDecorator: retry_loop
@patch('time.sleep')
def test_retry_loop_max_end_on_error(mock_time_sleep):
    """Retry loops until max and ends with error at end."""
    rd = RetryDecorator({'max': 3})
    context = Context({'k1': 'v1'})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with pytest.raises(ValueError) as err_info:
            rd.retry_loop(context, mock)

        assert str(err_info.value) == 'arb'

    assert context['retryCounter'] == 3
    assert rd.retry_counter == 3
    assert mock.call_count == 3
    mock.assert_called_with({'k1': 'v1', 'retryCounter': 3})

    assert mock_time_sleep.call_count == 2
    mock_time_sleep.assert_called_with(0)

    assert mock_logger_info.mock_calls == [
        call('retry decorator will try 3 times with fixed backoff starting at '
             '0s intervals.'),
        call('retry: running step with counter 1'),
        call('retry: running step with counter 2'),
        call('retry: running step with counter 3')]


@patch('time.sleep')
def test_retry_loop_max_end_on_error_substitution(mock_time_sleep):
    """Retry loops with substitution until max and ends with error at end."""
    rd = RetryDecorator({'max': PyString('3')})
    context = Context({'k1': 'v1'})
    mock = MagicMock()
    mock.side_effect = ValueError('arb')

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with pytest.raises(ValueError) as err_info:
            rd.retry_loop(context, mock)

        assert str(err_info.value) == 'arb'

    assert context['retryCounter'] == 3
    assert rd.retry_counter == 3
    assert mock.call_count == 3
    mock.assert_called_with({'k1': 'v1', 'retryCounter': 3})

    assert mock_time_sleep.call_count == 2
    mock_time_sleep.assert_called_with(0)

    assert mock_logger_info.mock_calls == [
        call('retry decorator will try 3 times with fixed backoff starting '
             'at 0s intervals.'),
        call('retry: running step with counter 1'),
        call('retry: running step with counter 2'),
        call('retry: running step with counter 3')]


@patch('time.sleep')
def test_retry_loop_max_continue_on_success(mock_time_sleep):
    """Retry loops breaks out of loop on success."""
    rd = RetryDecorator({'max': 3, 'sleep': 10.1})
    context = Context({'k1': 'v1'})
    mock = MagicMock()
    mock.side_effect = [ValueError('arb'), None]

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
            rd.retry_loop(context, mock)

    assert context['retryCounter'] == 2
    assert rd.retry_counter == 2
    assert mock.call_count == 2
    mock.assert_called_with({'k1': 'v1', 'retryCounter': 2})

    assert mock_time_sleep.call_count == 1
    mock_time_sleep.assert_called_with(10.1)

    mock_logger_debug.assert_any_call(
        'retry loop complete, reporting success.')

    assert mock_logger_info.mock_calls == [
        call('retry decorator will try 3 times with fixed backoff starting at '
             '10.1s intervals.'),
        call('retry: running step with counter 1'),
        call('retry: running step with counter 2')]


@patch('time.sleep')
def test_retry_loop_max_continue_on_success_fixed_list(mock_time_sleep):
    """Retry loops breaks out of loop on success with list input to fixed."""
    rd = RetryDecorator({'max': 5, 'sleep': [10.1, 10.2]})
    context = Context({'k1': 'v1'})
    mock = MagicMock()
    mock.side_effect = [ValueError('arb'),
                        ValueError('arb'),
                        ValueError('arb'),
                        None]

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with patch_logger('pypyr.dsl', logging.DEBUG) as mock_logger_debug:
            rd.retry_loop(context, mock)

    assert context['retryCounter'] == 4
    assert rd.retry_counter == 4
    assert mock.call_count == 4
    mock.assert_called_with({'k1': 'v1', 'retryCounter': 4})

    assert mock_time_sleep.call_count == 3
    # list cycles over last element
    mock_time_sleep.mock_calls == [call(10.1), call(10.2), call(10.2)]

    mock_logger_debug.assert_any_call(
        'retry loop complete, reporting success.')

    assert mock_logger_info.mock_calls == [
        call('retry decorator will try 5 times with fixed backoff starting at '
             '[10.1, 10.2]s intervals.'),
        call('retry: running step with counter 1'),
        call('retry: running step with counter 2'),
        call('retry: running step with counter 3'),
        call('retry: running step with counter 4')]


@patch('time.sleep')
def test_retry_loop_indefinite_continue_on_success(mock_time_sleep):
    """Retry loops breaks out of indefinite loop on success."""
    rd = RetryDecorator({'sleep': 10.1})
    context = Context({'k1': 'v1'})
    mock = MagicMock()
    mock.side_effect = [ValueError('arb1'), ValueError('arb2'), None]

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        rd.retry_loop(context, mock)

    assert context['retryCounter'] == 3
    assert rd.retry_counter == 3
    assert mock.call_count == 3
    mock.assert_called_with({'k1': 'v1', 'retryCounter': 3})

    assert mock_time_sleep.call_count == 2
    mock_time_sleep.assert_called_with(10.1)

    assert mock_logger_info.mock_calls == [
        call('retry decorator will try indefinitely with fixed backoff '
             'starting at 10.1s intervals.'),
        call('retry: running step with counter 1'),
        call('retry: running step with counter 2'),
        call('retry: running step with counter 3')]


@patch('time.sleep')
def test_retry_all_substitutions(mock_time_sleep):
    """Retry loop runs every param substituted."""
    rd = RetryDecorator({'max': '{k3[1][k031]}',
                         'sleep': '{k2}'})
    context = Context({'k1': False,
                       'k2': 0.3,
                       'k3': [
                           0,
                           {'k031': 1, 'k032': False}
                       ]})

    step_count = 0

    def mock_step(context):
        nonlocal step_count
        step_count += 1

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        rd.retry_loop(context, mock_step)

    assert context['retryCounter'] == 1
    assert rd.retry_counter == 1
    assert step_count == 1

    assert mock_time_sleep.call_count == 0

    assert mock_logger_info.mock_calls == [
        call('retry decorator will try 1 times with fixed backoff starting at '
             '0.3s intervals.'),
        call('retry: running step with counter 1')]


@patch('pypyr.retries.random.uniform', side_effect=[11, 12, 13])
@patch('time.sleep')
def test_retry_all_substitutions_backoff(mock_sleep, mock_random):
    """Retry loop runs every param substituted with non-default backoff."""
    rd = RetryDecorator({'max': '{k3[1][k031]}',
                         'sleep': '{k2}',
                         'backoff': '{k6}',
                         'jrc': '{k4}',
                         'sleepMax': '{k5}',
                         'backoffArgs': {'base': '{k7}', 'arb': '{k8}'}})
    context = Context({'k1': False,
                       'k2': 3,
                       'k3': [
                           0,
                           {'k031': 4, 'k032': False}
                       ],
                       'k4': 0.5,
                       'k5': 30,
                       'k6': 'exponentialjitter',
                       'k7': 3,
                       'k8': 'a value',
                       'step_count': 0})

    def mock_step(context):
        context['step_count'] += 1
        if context['step_count'] != 4:
            raise ValueError()

    rd.retry_loop(context, mock_step)

    assert context['retryCounter'] == 4
    assert rd.retry_counter == 4
    assert context['step_count'] == 4

    assert mock_sleep.mock_calls == [call(11), call(12), call(13)]
    assert mock_random.mock_calls == [call(4.5, 9),
                                      call(13.5, 27),
                                      call(15, 30)]


@patch('pypyr.retries.random.uniform', side_effect=[11, 12, 13])
@patch('time.sleep')
def test_retry_all_substitutions_backoff_jitter_list(mock_sleep, mock_random):
    """Retry loop runs fixed jitter with list."""
    rd = RetryDecorator({'max': '{k3[1][k031]}',
                         'sleep': '{k2}',
                         'backoff': '{k6}',
                         'jrc': '{k4}',
                         'sleepMax': '{k5}'})
    context = Context({'k1': False,
                       'k2': [0.3, 0.2, 0.1],
                       'k3': [
                           0,
                           {'k031': 4, 'k032': False}
                       ],
                       'k4': 2,
                       'k5': 0.25,
                       'k6': 'jitter',
                       'step_count': 0})

    def mock_step(context):
        context['step_count'] += 1
        if context['step_count'] != 4:
            raise ValueError()

    rd.retry_loop(context, mock_step)

    assert context['retryCounter'] == 4
    assert rd.retry_counter == 4
    assert context['step_count'] == 4

    assert mock_sleep.mock_calls == [call(11), call(12), call(13)]
    assert mock_random.mock_calls == [call(0.5, 0.25),
                                      call(0.4, 0.2),
                                      call(0.2, 0.1)]

# endregion RetryDecorator: retry_loop

# endregion RetryDecorator

# region WhileDecorator

# region WhileDecorator: init


def test_while_init_defaults_stop():
    """The WhileDecorator ctor sets defaults with only stop set."""
    wd = WhileDecorator({'stop': 'arb'})
    assert wd.stop == 'arb'
    assert wd.sleep == 0
    assert wd.max is None
    assert not wd.error_on_max
    assert wd.while_counter is None


def test_while_init_defaults_max():
    """The WhileDecorator ctor sets defaults with only max set."""
    wd = WhileDecorator({'max': 3})
    assert wd.stop is None
    assert wd.sleep == 0
    assert wd.max == 3
    assert not wd.error_on_max
    assert wd.while_counter is None


def test_while_init_all_attributes():
    """The WhileDecorator ctor with all props set."""
    wd = WhileDecorator(
        {'errorOnMax': True, 'max': 3, 'sleep': 4.4, 'stop': '5'})
    assert wd.stop == '5'
    assert wd.sleep == 4.4
    assert wd.max == 3
    assert wd.error_on_max
    assert wd.while_counter is None


def test_while_init_not_a_dict():
    """The WhileDecorator raises PipelineDefinitionError on bad ctor input."""
    with pytest.raises(PipelineDefinitionError) as err_info:
        WhileDecorator('arb')

    assert str(err_info.value) == (
        "while decorator must be a dict (i.e a map) type.")


def test_while_init_no_max_no_stop():
    """The WhileDecorator raises PipelineDefinitionError no max and no stop."""
    with pytest.raises(PipelineDefinitionError) as err_info:
        WhileDecorator({'arb': 'arbv'})

    assert str(err_info.value) == (
        "the while decorator must have either max or "
        "stop, or both. But not neither. Note that setting stop: False with "
        "no max is an infinite loop. If an infinite loop is really what you "
        "want, set stop: False")


# endregion WhileDecorator: init

# region WhileDecorator: exec_iteration
def test_while_exec_iteration_no_stop():
    """exec_iteration returns False when no stop condition given."""
    wd = WhileDecorator({'max': 3})

    context = Context({})
    mock = MagicMock()
    assert not wd.exec_iteration(2, context, mock)
    # context endures
    assert context['whileCounter'] == 2
    assert wd.while_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'whileCounter': 2})


def test_while_exec_iteration_stop_true():
    """exec_iteration returns True when stop is bool True."""
    wd = WhileDecorator({'stop': True})

    context = Context({})
    mock = MagicMock()
    assert wd.exec_iteration(2, context, mock)
    # context endures
    assert context['whileCounter'] == 2
    assert wd.while_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'whileCounter': 2})


def test_while_exec_iteration_stop_evals_true():
    """exec_iteration True when stop evals True from formatting expr."""
    wd = WhileDecorator({'stop': '{stop}'})

    context = Context({'stop': True})
    mock = MagicMock()
    assert wd.exec_iteration(2, context, mock)
    # context endures
    assert context['whileCounter'] == 2
    assert wd.while_counter == 2
    assert len(context) == 2
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'stop': True, 'whileCounter': 2})


def test_while_exec_iteration_stop_false():
    """exec_iteration False when stop is False."""
    wd = WhileDecorator({'max': 1, 'stop': False})

    context = Context()
    mock = MagicMock()
    assert not wd.exec_iteration(2, context, mock)
    # context endures
    assert context['whileCounter'] == 2
    assert wd.while_counter == 2
    assert len(context) == 1
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'whileCounter': 2})


def test_while_exec_iteration_stop_evals_false():
    """exec_iteration False when stop is False."""
    wd = WhileDecorator({'stop': '{stop}'})

    context = Context({'stop': False})
    mock = MagicMock()

    assert not wd.exec_iteration(2, context, mock)
    # context endures
    assert context['whileCounter'] == 2
    assert wd.while_counter == 2
    assert len(context) == 2
    # step_method called once and only once with updated context
    mock.assert_called_once_with({'stop': False, 'whileCounter': 2})

# endregion WhileDecorator: exec_iteration

# region WhileDecorator: while_loop


def test_while_loop_stop_true():
    """Stop True runs loop once because it only evals after 1st iteration."""
    wd = WhileDecorator({'stop': True})

    mock = MagicMock()

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        wd.while_loop(Context(), mock)

    mock.assert_called_once()

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop until True evaluates to True '
             'at 0.0s intervals.'),
        call('while: running step with counter 1'),
        call('while loop done, stop condition True evaluated True.')]

    assert wd.while_counter == 1


def test_while_loop_max_0():
    """Max 0 doesn't run even once."""
    wd = WhileDecorator({'max': 0})

    mock = MagicMock()

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        wd.while_loop(Context(), mock)

    mock.assert_not_called()

    assert mock_logger_info.mock_calls == [
        call('max 0 is 0. while only runs when max > 0.')]

    assert wd.while_counter == 0


def test_while_loop_max_0_with_formatting():
    """Max 0 doesn't run even once with formatting expression."""
    wd = WhileDecorator({'max': '{x}'})

    mock = MagicMock()

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        wd.while_loop(Context({'x': -3}), mock)

    mock.assert_not_called()

    assert mock_logger_info.mock_calls == [
        call('max {x} is -3. while only runs when max > 0.')]

    assert wd.while_counter == 0


def test_while_loop_stop_evals_true():
    """Stop evaluates True from formatting expr runs once."""
    wd = WhileDecorator({'stop': '{thisistrue}'})

    mock = MagicMock()

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        wd.while_loop(Context({'thisistrue': True}), mock)

    mock.assert_called_once()

    assert wd.while_counter == 1

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop until {thisistrue} evaluates to True '
             'at 0.0s intervals.'),
        call('while: running step with counter 1'),
        call('while loop done, stop condition {thisistrue} evaluated True.')]


def test_while_loop_no_stop_no_max():
    """No stop, no max should raise error."""
    wd = WhileDecorator({'stop': True})
    wd.max = None
    wd.stop = None

    mock = MagicMock()
    with pytest.raises(PipelineDefinitionError) as err_info:
        wd.while_loop(Context(), mock)

    mock.assert_not_called()
    assert str(err_info.value) == (
        "the while decorator must have either max or "
        "stop, or both. But not neither.")


@patch('time.sleep')
def test_while_loop_max_no_stop(mock_time_sleep):
    """While loop runs with max but no stop."""
    wd = WhileDecorator({'max': 3})
    context = Context({'k1': 'v1'})
    mock = MagicMock()

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        wd.while_loop(context, mock)

    assert context['whileCounter'] == 3
    assert wd.while_counter == 3
    assert mock.call_count == 3
    mock.assert_called_with({'k1': 'v1', 'whileCounter': 3})

    assert mock_time_sleep.call_count == 2
    mock_time_sleep.assert_called_with(0)

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 3 times at 0.0s intervals.'),
        call('while: running step with counter 1'),
        call('while: running step with counter 2'),
        call('while: running step with counter 3')]


@patch('time.sleep')
def test_while_loop_stop_no_max(mock_time_sleep):
    """While loop runs with stop but no max."""
    wd = WhileDecorator({'stop': '{k1}', 'sleep': '{k2}'})
    context = Context({'k1': False, 'k2': 0.3})

    step_count = 0
    step_context = []

    def mock_step(context):
        nonlocal step_count, step_context
        step_count += 1
        step_context.append(deepcopy(context))
        if context['whileCounter'] == 3:
            context['k1'] = True

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        wd.while_loop(context, mock_step)

    assert context['whileCounter'] == 3
    assert wd.while_counter == 3
    assert step_count == 3
    assert step_context == [{'k1': False, 'k2': 0.3, 'whileCounter': 1},
                            {'k1': False, 'k2': 0.3, 'whileCounter': 2},
                            {'k1': False, 'k2': 0.3, 'whileCounter': 3}]

    assert mock_time_sleep.call_count == 2
    mock_time_sleep.assert_called_with(0.3)

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop until {k1} evaluates to True at 0.3s '
             'intervals.'),
        call('while: running step with counter 1'),
        call('while: running step with counter 2'),
        call('while: running step with counter 3'),
        call('while loop done, stop condition {k1} evaluated True.')]


@patch('time.sleep')
def test_while_loop_stop_and_max_stop_before_max(mock_time_sleep):
    """While loop runs with stop and max, exit before max."""
    wd = WhileDecorator({'max': 5, 'stop': '{k1}', 'sleep': '{k2}'})
    context = Context({'k1': False, 'k2': 0.3})

    step_count = 0
    step_context = []

    def mock_step(context):
        nonlocal step_count, step_context
        step_count += 1
        step_context.append(deepcopy(context))
        if context['whileCounter'] == 3:
            context['k1'] = True

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        wd.while_loop(context, mock_step)

    assert context['whileCounter'] == 3
    assert wd.while_counter == 3
    assert step_count == 3
    assert step_context == [{'k1': False, 'k2': 0.3, 'whileCounter': 1},
                            {'k1': False, 'k2': 0.3, 'whileCounter': 2},
                            {'k1': False, 'k2': 0.3, 'whileCounter': 3}]

    assert mock_time_sleep.call_count == 2
    mock_time_sleep.assert_called_with(0.3)

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 5 times, or until {k1} evaluates to '
             'True at 0.3s intervals.'),
        call('while: running step with counter 1'),
        call('while: running step with counter 2'),
        call('while: running step with counter 3'),
        call('while loop done, stop condition {k1} evaluated True.')]


@patch('time.sleep')
def test_while_loop_stop_and_max_exhaust_max(mock_time_sleep):
    """While loop runs with stop and max, exhaust max."""
    wd = WhileDecorator({'max': 3, 'stop': '{k1}', 'sleep': '{k2}'})
    context = Context({'k1': False, 'k2': 0.3})

    step_count = 0
    step_context = []

    def mock_step(context):
        nonlocal step_count, step_context
        step_count += 1
        step_context.append(deepcopy(context))

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        wd.while_loop(context, mock_step)

    assert context['whileCounter'] == 3
    assert wd.while_counter == 3
    assert step_count == 3
    assert step_context == [{'k1': False, 'k2': 0.3, 'whileCounter': 1},
                            {'k1': False, 'k2': 0.3, 'whileCounter': 2},
                            {'k1': False, 'k2': 0.3, 'whileCounter': 3}]

    assert mock_time_sleep.call_count == 2
    mock_time_sleep.assert_called_with(0.3)

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 3 times, or until {k1} evaluates to '
             'True at 0.3s intervals.'),
        call('while: running step with counter 1'),
        call('while: running step with counter 2'),
        call('while: running step with counter 3'),
        call('while decorator looped 3 times, and {k1} never evaluated to '
             'True.')]


@patch('time.sleep')
def test_while_loop_stop_and_max_exhaust_error(mock_time_sleep):
    """While loop runs with stop and max, exhaust max."""
    wd = WhileDecorator({'max': 3,
                         'stop': '{k1}',
                         'sleep': '{k2}',
                         'errorOnMax': '{k3}'})
    context = Context({'k1': False, 'k2': 0.3, 'k3': True})

    step_count = 0
    step_context = []

    def mock_step(context):
        nonlocal step_count, step_context
        step_count += 1
        step_context.append(deepcopy(context))

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
            with pytest.raises(LoopMaxExhaustedError) as err_info:
                wd.while_loop(context, mock_step)

    assert str(err_info.value) == (
        "while loop reached 3 and {k1} never evaluated to True.")

    assert context['whileCounter'] == 3
    assert wd.while_counter == 3
    assert step_count == 3
    assert step_context == [{'k1': False,
                             'k2': 0.3,
                             'k3': True,
                             'whileCounter': 1},
                            {'k1': False,
                             'k2': 0.3,
                             'k3': True,
                             'whileCounter': 2},
                            {'k1': False,
                             'k2': 0.3,
                             'k3': True,
                             'whileCounter': 3}]

    assert mock_time_sleep.call_count == 2
    mock_time_sleep.assert_called_with(0.3)

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 3 times, or until {k1} evaluates to '
             'True at 0.3s intervals.'),
        call('while: running step with counter 1'),
        call('while: running step with counter 2'),
        call('while: running step with counter 3')]

    assert mock_logger_error.mock_calls == [
        call('exhausted 3 iterations of while loop, and errorOnMax is True.')
    ]


@patch('time.sleep')
def test_while_loop_max_exhaust_error(mock_time_sleep):
    """While loop runs with only max, exhaust max."""
    wd = WhileDecorator({'max': 3,
                         'sleep': '{k2}',
                         'errorOnMax': True})
    context = Context({'k1': False, 'k2': 0.3, 'k3': True})

    step_count = 0
    step_context = []

    def mock_step(context):
        nonlocal step_count, step_context
        step_count += 1
        step_context.append(deepcopy(context))

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        with patch_logger('pypyr.dsl', logging.ERROR) as mock_logger_error:
            with pytest.raises(LoopMaxExhaustedError) as err_info:
                wd.while_loop(context, mock_step)

    assert str(err_info.value) == "while loop reached 3."

    assert context['whileCounter'] == 3
    assert wd.while_counter == 3
    assert step_count == 3
    assert step_context == [{'k1': False,
                             'k2': 0.3,
                             'k3': True,
                             'whileCounter': 1},
                            {'k1': False,
                             'k2': 0.3,
                             'k3': True,
                             'whileCounter': 2},
                            {'k1': False,
                             'k2': 0.3,
                             'k3': True,
                             'whileCounter': 3}]

    assert mock_time_sleep.call_count == 2
    mock_time_sleep.assert_called_with(0.3)

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 3 times at 0.3s intervals.'),
        call('while: running step with counter 1'),
        call('while: running step with counter 2'),
        call('while: running step with counter 3')]

    assert mock_logger_error.mock_calls == [
        call('exhausted 3 iterations of while loop, and errorOnMax is True.')
    ]


@patch('time.sleep')
def test_while_loop_all_substitutions(mock_time_sleep):
    """While loop runs every param substituted."""
    wd = WhileDecorator({'max': '{k3[1][k031]}',
                         'stop': '{k1}',
                         'sleep': '{k2}',
                         'errorOnMax': '{k3[1][k032]}'})
    context = Context({'k1': False,
                       'k2': 0.3,
                       'k3': [
                           0,
                           {'k031': 1, 'k032': False}
                       ]})

    step_count = 0

    def mock_step(context):
        nonlocal step_count
        step_count += 1

    with patch_logger('pypyr.dsl', logging.INFO) as mock_logger_info:
        wd.while_loop(context, mock_step)

    assert context['whileCounter'] == 1
    assert wd.while_counter == 1
    assert step_count == 1

    assert mock_time_sleep.call_count == 0

    assert mock_logger_info.mock_calls == [
        call('while decorator will loop 1 times, or until {k1} evaluates to '
             'True at 0.3s intervals.'),
        call('while: running step with counter 1'),
        call('while decorator looped 1 times, and {k1} never evaluated to '
             'True.')]
# endregion WhileDecorator: while_loop
# endregion WhileDecorator
