"""fileinoutrewriter.py unit tests."""
import pytest
from unittest.mock import call, Mock, patch
from pypyr.context import Context
from pypyr.errors import KeyNotInContextError
from pypyr.steps.dsl.fileinoutrewriter import (FileInRewriterStep,
                                               ObjectRewriterStep,
                                               StreamRewriterStep,
                                               StreamReplacePairsRewriterStep)
from pypyr.utils.filesystem import (ObjectRepresenter,
                                    ObjectRewriter,
                                    FileRewriter,
                                    StreamRewriter)

# region FileInRewriterStep


def test_fileinrewriterstep_root_required():
    """Key root must exist."""
    context = Context({'root': 'blah'})

    with pytest.raises(KeyNotInContextError) as err:
        FileInRewriterStep('blah.name', 'Xroot', context)

    assert str(err.value) == (
        "context['Xroot'] doesn't exist. It must exist for blah.name.")


def test_fileinrewriterstep_in_required():
    """Key in must exist."""
    context = Context({'root': 'blah'})

    with pytest.raises(KeyNotInContextError) as err:
        FileInRewriterStep('blah.name', 'root', context)

    assert str(err.value) == ("context['root']['in'] "
                              "doesn't exist. It must exist for "
                              "blah.name.")


def test_fileinrewriterstep_in_not_out():
    """File rewriter step instantiates with in but no out."""
    context = Context({'root': {'in': 'inpathhere'}})

    obj = FileInRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathhere'
    assert not obj.path_out
    assert obj.context == context
    assert obj.logger.name == 'blah.name'


def test_fileinrewriterstep_in_and_out():
    """File rewriter step instantiates with in and out."""
    context = Context({'root': {'in': 'inpathhere', 'out': 'outpathhere'}})

    obj = FileInRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathhere'
    assert obj.path_out == 'outpathhere'
    assert obj.context == context
    assert obj.logger.name == 'blah.name'


def test_fileinrewriterstep_in_and_out_with_formatting():
    """File rewriter step instantiates with in and out applies formatting."""
    context = Context({'k1': 'v1',
                       'root': {'in': 'inpath{k1}here',
                                'out': 'outpath{k1}here'}})

    obj = FileInRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathv1here'
    assert obj.path_out == 'outpathv1here'
    assert obj.context == context
    assert obj.logger.name == 'blah.name'


def test_fileinrewriterstep_in_list_and_out_with_formatting():
    """File rewriter step instantiates in list & out applies formatting."""
    context = Context({'k1': 'v1',
                       'root': {'in': ['inpath{k1}here', '2', '{k1}'],
                                'out': 'outpath{k1}here'}})

    obj = FileInRewriterStep('blah.name', 'root', context)
    assert obj.path_in == ['inpathv1here', '2', 'v1']
    assert obj.path_out == 'outpathv1here'
    assert obj.context == context
    assert obj.logger.name == 'blah.name'


def test_fileinrewriterstep_run_step():
    """File rewriter runs files_in_to_out on rewriter."""
    context = Context({'root': {'in': 'inpathhere', 'out': 'outpathhere'}})

    obj = FileInRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathhere'
    assert obj.path_out == 'outpathhere'
    assert obj.context == context
    assert obj.logger.name == 'blah.name'

    mock_rewriter = Mock(spec=FileRewriter)
    obj.run_step(mock_rewriter)
    mock_rewriter.files_in_to_out.assert_called_once_with(
        in_path='inpathhere',
        out_path='outpathhere')


def test_fileinrewriterstep_run_step_no_out():
    """File rewriter runs files_in_to_out on rewriter with no out."""
    context = Context({'root': {'in': 'inpathhere'}})

    obj = FileInRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathhere'
    assert not obj.path_out
    assert obj.context == context
    assert obj.logger.name == 'blah.name'

    mock_rewriter = Mock(spec=FileRewriter)
    obj.run_step(mock_rewriter)
    mock_rewriter.files_in_to_out.assert_called_once_with(
        in_path='inpathhere',
        out_path=None)


def test_fileinrewriterstep_encoding_default():
    """Default encoding from config."""
    context = Context({'root': {'in': 'inpathhere'}})

    with patch('pypyr.config.config.default_encoding', 'arb'):
        obj = FileInRewriterStep('blah.name', 'root', context)

    assert obj.path_in == 'inpathhere'
    assert not obj.path_out
    assert obj.context == context
    assert obj.logger.name == 'blah.name'

    assert obj.encoding_in == 'arb'
    assert obj.encoding_out == 'arb'


def test_fileinrewriterstep_encoding_in():
    """Explicitly set encoding in."""
    context = Context({'root': {'in': 'inpathhere', 'encodingIn': 'arbIn'}})

    with patch('pypyr.config.config.default_encoding', 'arb'):
        obj = FileInRewriterStep('blah.name', 'root', context)

    assert obj.path_in == 'inpathhere'
    assert not obj.path_out
    assert obj.context == context
    assert obj.logger.name == 'blah.name'

    assert obj.encoding_in == 'arbIn'
    assert obj.encoding_out == 'arb'


def test_fileinrewriterstep_encoding_out():
    """Explicitly set encoding out."""
    context = Context({'root': {'in': 'inpathhere', 'encodingOut': 'arbOut'}})

    with patch('pypyr.config.config.default_encoding', 'arb'):
        obj = FileInRewriterStep('blah.name', 'root', context)

    assert obj.path_in == 'inpathhere'
    assert not obj.path_out
    assert obj.context == context
    assert obj.logger.name == 'blah.name'

    assert obj.encoding_in == 'arb'
    assert obj.encoding_out == 'arbOut'


def test_fileinrewriterstep_encoding_in_out():
    """Explicitly set encoding in & out."""
    context = Context({'root': {'in': 'inpathhere',
                                'encodingIn': 'arbIn',
                                'encodingOut': 'arbOut'}})

    with patch('pypyr.config.config.default_encoding', 'arb'):
        obj = FileInRewriterStep('blah.name', 'root', context)

    assert obj.path_in == 'inpathhere'
    assert not obj.path_out
    assert obj.context == context
    assert obj.logger.name == 'blah.name'

    assert obj.encoding_in == 'arbIn'
    assert obj.encoding_out == 'arbOut'


def test_fileinrewriterstep_encoding_substitutions_in_out():
    """Encoding works with substitutions for in and out."""
    context = Context({
        'encIn': 'arbIn',
        'encOut': 'arbOut',
        'root': {'in': 'inpathhere',
                 'encodingIn': '{encIn}',
                 'encodingOut': '{encOut}'}})

    with patch('pypyr.config.config.default_encoding', 'arb'):
        obj = FileInRewriterStep('blah.name', 'root', context)

    assert obj.path_in == 'inpathhere'
    assert not obj.path_out
    assert obj.context == context
    assert obj.logger.name == 'blah.name'

    assert obj.encoding_in == 'arbIn'
    assert obj.encoding_out == 'arbOut'


def test_fileinrewriterstep_bare_encoding_substitutions():
    """Encoding works with substitutions for bare encoding."""
    context = Context({
        'enc': 'arbenc',
        'root': {'in': 'inpathhere',
                 'encoding': '{enc}'}})

    with patch('pypyr.config.config.default_encoding', 'arb'):
        obj = FileInRewriterStep('blah.name', 'root', context)

    assert obj.path_in == 'inpathhere'
    assert not obj.path_out
    assert obj.context == context
    assert obj.logger.name == 'blah.name'

    assert obj.encoding_in == 'arbenc'
    assert obj.encoding_out == 'arbenc'
# endregion FileInRewriterStep

# region ObjectRewriterStep


@patch('pypyr.steps.dsl.fileinoutrewriter.ObjectRewriter', spec=FileRewriter)
def test_objectrewriterstep_run_step(mock_rewriter):
    """Object rewriter runs files_in_to_out on object rewriter."""
    context = Context({'root': {'in': 'inpathhere',
                                'out': 'outpathhere',
                                'encodingIn': 'encIn',
                                'encodingOut': 'encOut'}})

    obj = ObjectRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathhere'
    assert obj.path_out == 'outpathhere'
    assert obj.context == context
    assert obj.logger.name == 'blah.name'
    assert obj.encoding_in == 'encIn'
    assert obj.encoding_out == 'encOut'

    mock_representer = Mock(spec=ObjectRepresenter)
    obj.run_step(mock_representer)

    # assert_called from mock will never think the generator/iter are equal,
    # hence assert by hand.
    assert mock_rewriter.mock_calls[0] == call(context.get_formatted_value,
                                               mock_representer,
                                               encoding_in='encIn',
                                               encoding_out='encOut')

    mock_rewriter.return_value.files_in_to_out.assert_called_once_with(
        in_path='inpathhere',
        out_path='outpathhere')


@patch('pypyr.steps.dsl.fileinoutrewriter.ObjectRewriter', spec=ObjectRewriter)
def test_objectrewriterstep_run_step_no_out(mock_rewriter):
    """Object rewriter runs files_in_to_out on object rewriter with no out."""
    context = Context({'root': {'in': 'inpathhere'}})

    obj = ObjectRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathhere'
    assert not obj.path_out
    assert obj.context == context
    assert obj.logger.name == 'blah.name'

    mock_representer = Mock(spec=ObjectRepresenter)
    obj.run_step(mock_representer)

    # assert_called from mock will never think the generator/iter are equal,
    # hence assert by hand.
    assert mock_rewriter.mock_calls[0] == call(context.get_formatted_value,
                                               mock_representer,
                                               encoding_in=None,
                                               encoding_out=None)

    mock_rewriter.return_value.files_in_to_out.assert_called_once_with(
        in_path='inpathhere',
        out_path=None)
# endregion ObjectRewriterStep

# region StreamRewriterStep


@patch('pypyr.steps.dsl.fileinoutrewriter.StreamRewriter', spec=FileRewriter)
def test_streamrewriterstep_run_step(mock_rewriter):
    """Stream rewriter runs files_in_to_out on stream rewriter."""
    context = Context({'root': {'in': 'inpathhere',
                                'out': 'outpathhere',
                                'encodingIn': 'encIn',
                                'encodingOut': 'encOut'}})

    obj = StreamRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathhere'
    assert obj.path_out == 'outpathhere'
    assert obj.context == context
    assert obj.logger.name == 'blah.name'
    assert obj.encoding_in == 'encIn'
    assert obj.encoding_out == 'encOut'

    obj.run_step()

    # assert_called from mock will never think the generator/iter are equal,
    # hence assert by hand.
    assert mock_rewriter.mock_calls[0] == call(context.iter_formatted_strings,
                                               encoding_in='encIn',
                                               encoding_out='encOut')

    mock_rewriter.return_value.files_in_to_out.assert_called_once_with(
        in_path='inpathhere',
        out_path='outpathhere')


@patch('pypyr.steps.dsl.fileinoutrewriter.StreamRewriter', spec=StreamRewriter)
def test_streamrewriterstep_run_step_no_out(mock_rewriter):
    """Stream rewriter runs files_in_to_out on stream rewriter."""
    context = Context({'root': {'in': 'inpathhere', 'out': None}})

    obj = StreamRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathhere'
    assert not obj.path_out
    assert obj.context == context
    assert obj.logger.name == 'blah.name'

    obj.run_step()

    # assert_called from mock will never think the generator/iter are equal,
    # hence assert by hand.
    assert mock_rewriter.mock_calls[0] == call(context.iter_formatted_strings,
                                               encoding_in=None,
                                               encoding_out=None)

    mock_rewriter.return_value.files_in_to_out.assert_called_once_with(
        in_path='inpathhere',
        out_path=None)
# endregion StreamRewriterStep

# region StreamReplacePairsRewriterStep


@patch('pypyr.steps.dsl.fileinoutrewriter.StreamRewriter', spec=StreamRewriter)
def test_streamreplacepairsrewriterstep_run_step(mock_rewriter):
    """Stream replace pairs rewriter runs files_in_to_out."""
    context = Context({'root': {'in': 'inpathhere',
                                'out': 'outpathhere',
                                'replacePairs': {
                                    'a': 'b',
                                    'c': 'd'
                                },
                                'encodingIn': 'encIn',
                                'encodingOut': 'encOut'}})

    obj = StreamReplacePairsRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathhere'
    assert obj.path_out == 'outpathhere'
    assert obj.context == context
    assert obj.logger.name == 'blah.name'
    assert obj.replace_pairs == {'a': 'b', 'c': 'd'}
    assert obj.encoding_in == 'encIn'
    assert obj.encoding_out == 'encOut'

    iter_replace_strings_target = ('pypyr.steps.dsl.fileinoutrewriter.'
                                   'StreamReplacePairsRewriterStep.'
                                   'iter_replace_strings')
    with patch(iter_replace_strings_target) as mock_iter:
        obj.run_step()

    # the rewriter should've been instantiated with the iter_replace_strings
    # function.
    mock_iter.assert_called_once_with({'a': 'b', 'c': 'd'})
    assert mock_rewriter.mock_calls[0] == call(mock_iter.return_value,
                                               encoding_in='encIn',
                                               encoding_out='encOut')

    mock_rewriter.return_value.files_in_to_out.assert_called_once_with(
        in_path='inpathhere',
        out_path='outpathhere')


@patch('pypyr.steps.dsl.fileinoutrewriter.StreamRewriter', spec=StreamRewriter)
def test_streamreplacepairsrewriterstep_run_step_substitutions(mock_rewriter):
    """Stream replace pairs rewriter files_in_to_out with substitutions."""
    context = Context({
        'k1': 'b',
        'k2': 'd',
        'k3': '{k2}',
        'root': {'in': 'inpathhere',
                 'out': 'outpathhere',
                 'replacePairs': {
                     'a': '{k1}',
                     'c': '{k3}'
                 },
                 'encodingIn': 'encIn',
                 'encodingOut': 'encOut'}})

    obj = StreamReplacePairsRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathhere'
    assert obj.path_out == 'outpathhere'
    assert obj.context == context
    assert obj.logger.name == 'blah.name'
    assert obj.replace_pairs == {'a': 'b', 'c': 'd'}
    assert obj.encoding_in == 'encIn'
    assert obj.encoding_out == 'encOut'

    iter_replace_strings_target = ('pypyr.steps.dsl.fileinoutrewriter.'
                                   'StreamReplacePairsRewriterStep.'
                                   'iter_replace_strings')
    with patch(iter_replace_strings_target) as mock_iter:
        obj.run_step()

    # the rewriter should've been instantiated with the iter_replace_strings
    # function.
    mock_iter.assert_called_once_with({'a': 'b', 'c': 'd'})
    assert mock_rewriter.mock_calls[0] == call(mock_iter.return_value,
                                               encoding_in='encIn',
                                               encoding_out='encOut')

    mock_rewriter.return_value.files_in_to_out.assert_called_once_with(
        in_path='inpathhere',
        out_path='outpathhere')


@patch('pypyr.steps.dsl.fileinoutrewriter.StreamRewriter', spec=StreamRewriter)
def test_streamreplacepairsrewriterstep_run_step_no_out(mock_rewriter):
    """Stream replace pairs rewriter runs files_in_to_out with no out."""
    context = Context({'root': {'in': 'inpathhere',
                                'replacePairs': {
                                    'a': 'b',
                                    'c': 'd'
                                },
                                'encoding': 'arb'}})

    obj = StreamReplacePairsRewriterStep('blah.name', 'root', context)
    assert obj.path_in == 'inpathhere'
    assert not obj.path_out
    assert obj.context == context
    assert obj.logger.name == 'blah.name'
    assert obj.replace_pairs == {'a': 'b', 'c': 'd'}
    assert obj.encoding_in == 'arb'
    assert obj.encoding_out == 'arb'

    iter_replace_strings_target = ('pypyr.steps.dsl.fileinoutrewriter.'
                                   'StreamReplacePairsRewriterStep.'
                                   'iter_replace_strings')
    with patch(iter_replace_strings_target) as mock_iter:
        obj.run_step()

    # the rewriter should've been instantiated with the iter_replace_strings
    # function.
    mock_iter.assert_called_once_with({'a': 'b', 'c': 'd'})
    assert mock_rewriter.mock_calls[0] == call(mock_iter.return_value,
                                               encoding_in='arb',
                                               encoding_out='arb')

    mock_rewriter.return_value.files_in_to_out.assert_called_once_with(
        in_path='inpathhere',
        out_path=None)

# region iter_replace_strings


def test_iter_replace_string_empties():
    """Nothing in, nothing out."""
    in_string = ''
    replace_pairs = {}
    result = StreamReplacePairsRewriterStep.iter_replace_strings(replace_pairs)
    assert not list(result(in_string))


def test_iter_replace_string_one_none():
    """One in, none out."""
    in_string = ['one two three four five six seven eight']
    replace_pairs = {'ten': '10'}
    result = StreamReplacePairsRewriterStep.iter_replace_strings(replace_pairs)
    assert list(result(in_string)) == in_string


def test_iter_replace_string_one_one():
    """One in, one out."""
    in_string = ['one two three four five six seven eight']
    replace_pairs = {'six': '6'}
    result = StreamReplacePairsRewriterStep.iter_replace_strings(replace_pairs)
    assert list(result(in_string))[
        0] == 'one two three four five 6 seven eight'


def test_iter_replace_string_two_one():
    """Two in, one out."""
    in_string = ['one two three four five six seven eight']
    replace_pairs = {'six': '6', 'XXX': '3'}
    result = StreamReplacePairsRewriterStep.iter_replace_strings(replace_pairs)
    assert list(result(in_string))[
        0] == 'one two three four five 6 seven eight'


def test_iter_replace_string_two_two():
    """Two in, two out."""
    in_string = ['one two three four five six seven eight']
    replace_pairs = {'six': '6', 'three': '3'}
    result = StreamReplacePairsRewriterStep.iter_replace_strings(replace_pairs)
    assert list(result(in_string))[0] == 'one two 3 four five 6 seven eight'


def test_iter_replace_string_instring_actually_iterates():
    """Iterates over an in iterable."""
    in_string = ['one two three', 'four five six', 'seven eight nine']
    replace_pairs = {'six': '6', 'three': '3'}
    func = StreamReplacePairsRewriterStep.iter_replace_strings(replace_pairs)
    result = list(func(in_string))
    assert result[0] == 'one two 3'
    assert result[1] == 'four five 6'
    assert result[2] == 'seven eight nine'


def test_iter_replace_string_later_replace_earlier():
    """A later replacement replaces one from earlier."""
    in_string = ['one two three', 'four five six', 'seven eight nine']
    replace_pairs = {'six': '6', 'three': '3', '6': 'XXX'}
    func = StreamReplacePairsRewriterStep.iter_replace_strings(replace_pairs)
    result = list(func(in_string))
    assert result[0] == 'one two 3'
    assert result[1] == 'four five XXX'
    assert result[2] == 'seven eight nine'

# endregion iter_replace_strings

# endregion StreamReplacePairsRewriterStep
