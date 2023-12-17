"""pipedef.py unit tests.

For PipelineBody unit tests, see stepsrunner_test.py.
"""
import pytest

from pypyr.context import Context
from pypyr.errors import PipelineDefinitionError
from pypyr.pipedef import (Metadata,
                           PipelineBody,
                           PipelineDefinition,
                           PipelineInfo,
                           PipelineFileInfo)

# region PipelineDefinition


def test_pipelinedefinition_eq():
    """Check PipelineDefinition equality."""
    assert (PipelineDefinition(pipeline='pipe', info='info')
            == PipelineDefinition(pipeline='pipe', info='info'))
    assert (PipelineDefinition(pipeline='pipe', info='info')
            != PipelineDefinition(pipeline='pipe2', info='info2'))
    assert PipelineDefinition(pipeline='pipe', info='info') != 1

# endregion PipelineDefinition

# region PipelineInfo


def test_pipelineinfo_ctor():
    """Test PipelineInfo constructor defaults."""
    pi = PipelineInfo(pipeline_name='arbpipe',
                      parent='arbdir',
                      loader='arbloader')

    assert pi.pipeline_name == 'arbpipe'
    assert pi.parent == 'arbdir'
    assert pi.loader == 'arbloader'
    assert pi.is_parent_cascading
    assert pi.is_loader_cascading


def test_pipelineinfo_no_cascade():
    """Test PipelineInfo constructor no cascade."""
    pi = PipelineInfo(pipeline_name='arbpipe',
                      parent='arbdir',
                      loader='arbloader',
                      is_parent_cascading=False,
                      is_loader_cascading=False)

    assert pi.pipeline_name == 'arbpipe'
    assert pi.parent == 'arbdir'
    assert pi.loader == 'arbloader'
    assert not pi.is_parent_cascading
    assert not pi.is_loader_cascading


def test_pipelineinfo_eq():
    """Check PipelineInfo equality."""
    assert (PipelineInfo(pipeline_name='arbpipe',
                         parent='arbdir',
                         loader='arbloader')
            == PipelineInfo(pipeline_name='arbpipe',
                            parent='arbdir',
                            loader='arbloader'))

    assert (PipelineInfo(pipeline_name='arbpipe',
                         parent='arbdir',
                         loader='arbloader')
            != PipelineInfo(pipeline_name='arbpipe',
                            parent='arbdir2',
                            loader='arbloader'))

    assert PipelineInfo(pipeline_name='arbpipe',
                        parent='arbdir',
                        loader='arbloader') != 2
# endregion PipelineInfo

# region PipelineFileInfo


def test_pipelinefileinfo_ctor():
    """Test PipelineFileInfo constructor defaults."""
    pi = PipelineFileInfo(pipeline_name='arbpipe',
                          loader='arbloader',
                          parent='arbdir',
                          path='arbpath')

    assert pi.pipeline_name == 'arbpipe'
    assert pi.parent == 'arbdir'
    assert pi.loader == 'arbloader'
    assert pi.path == 'arbpath'
    assert pi.is_parent_cascading
    assert pi.is_loader_cascading


def test_pipelinefileinfo_eq():
    """Check PipelineInfo equality."""
    assert (PipelineFileInfo(pipeline_name='arbpipe',
                             loader='arbloader',
                             parent='arbdir',
                             path='arbpath')
            == PipelineFileInfo(pipeline_name='arbpipe',
                                loader='arbloader',
                                parent='arbdir',
                                path='arbpath'))

    assert (PipelineFileInfo(pipeline_name='arbpipe',
                             loader='arbloader',
                             parent='arbdir',
                             path='arbpath')
            != PipelineFileInfo(pipeline_name='arbpipe',
                                loader='arbloader',
                                parent='arbdir2',
                                path='arbpath'))

    assert (PipelineFileInfo(pipeline_name='arbpipe',
                             loader='arbloader',
                             parent='arbdir',
                             path='arbpath')
            != PipelineFileInfo(pipeline_name='arbpipe',
                                loader='arbloader',
                                parent='arbdir',
                                path='arbpath2'))

    assert (PipelineFileInfo(pipeline_name='arbpipe',
                             loader='arbloader',
                             parent='arbdir',
                             path='arbpath')
            != PipelineInfo(pipeline_name='arbpipe',
                            parent='arbdir',
                            loader='arbloader'))

    assert PipelineFileInfo(pipeline_name='arbpipe',
                            loader='arbloader',
                            parent='arbdir',
                            path='arbpath') != 2
# endregion PipelineFileInfo

# region Metadata


def test_metadata_all_props():
    """Instantiate metadata with all properties."""
    md = Metadata({'author': 'arb author',
                   'help': 'arb help',
                   'version': 'arb version',
                   'arb': 'arb'})

    assert md
    assert md.author == 'arb author'
    assert md.help == 'arb help'
    assert md.version == 'arb version'
    assert md.get('arb') == 'arb'


def test_metadata_from_mapping():
    """Instantiate metadata with all properties with factory."""
    md = Metadata.from_mapping({'author': 'arb author',
                                'help': 'arb help',
                                'version': 'arb version',
                                'arb': 'arb'})

    assert md
    assert md.author == 'arb author'
    assert md.help == 'arb help'
    assert md.version == 'arb version'
    assert md.get('arb') == 'arb'


def test_metadata_from_mapping_raise_on_non_mapping():
    """Instantiate metadata with wrong type should raise."""
    with pytest.raises(PipelineDefinitionError) as err:
        Metadata.from_mapping([])

    assert str(err.value) == '_meta must be a mapping, not a list.'


def test_metadata_from_mapping_on_none():
    """Instantiate from None should raise."""
    with pytest.raises(PipelineDefinitionError) as err:
        Metadata.from_mapping(None)

    assert str(err.value) == '_meta must be a mapping, not a NoneType.'


def test_metadata_eq():
    """Assert metadata equality on equal instances."""
    assert Metadata({'arb': 123}) == Metadata({'arb': 123})
    assert Metadata({'arb': 123}) != Metadata({'arb': 456})
    assert Metadata({}) != 123


def test_metadata_empty():
    """Instantiate metadata no properties."""
    md = Metadata({})

    assert md
    assert md.author is None
    assert md.help is None
    assert md.version is None
    assert md.get('arb') is None


def test_metadata_none():
    """Instantiate metadata None."""
    md = Metadata(None)

    assert md
    assert md.author is None
    assert md.help is None
    assert md.version is None
    assert md.get('arb') is None

# endregion Metadata

# region PipelineBody


def test_pipeline_body_from_mapping_step_group_not_list_raises():
    """Raise error if step-group is not a list."""
    with pytest.raises(PipelineDefinitionError) as err:
        PipelineBody.from_mapping({'sg': 123})

    assert str(err.value) == ("step group 'sg' must be a sequence "
                              + "(aka list or array), but it is a int.")


def test_pipeline_body_from_mapping_step_group_is_string_raises():
    """Raise error if step-group is a string."""
    with pytest.raises(PipelineDefinitionError) as err:
        PipelineBody.from_mapping({'sg': '123'})

    assert str(err.value) == ("step group 'sg' must be a sequence "
                              + "(aka list or array), but it is a str.")


def test_pipeline_body_not_equal_raises():
    """Raise error if PipelineBody equality on different type."""
    assert PipelineBody.from_mapping({}) != 123
    assert PipelineBody.from_mapping(
        {}) != PipelineBody.from_mapping({'a': []})


def test_test_pipeline_body_create_custom_step_group_and_append():
    """Create a custom step group and append to it."""
    pb = PipelineBody()
    pb.create_custom_step_group('a', [1, 2, 3])
    assert pb.step_groups == {'a': [1, 2, 3]}
    pb.custom_step_group_append_step('a', 4)
    assert pb.step_groups == {'a': [1, 2, 3, 4]}

    # and append if step-group don't exist yet
    pb.custom_step_group_append_step('b', 5)
    assert pb.step_groups == {'a': [1, 2, 3, 4], 'b': [5]}


def test_test_pipeline_body_create_success_group_and_append():
    """Create a success step group and append to it."""
    pb = PipelineBody()
    pb.create_success_group([1, 2, 3])
    assert pb.step_groups == {'on_success': [1, 2, 3]}
    pb.success_append_step(4)
    assert pb.step_groups == {'on_success': [1, 2, 3, 4]}


def test_test_pipeline_body_create_failure_group_and_append():
    """Create a failure step group and append to it."""
    pb = PipelineBody()
    pb.create_failure_group([1, 2, 3])
    assert pb.step_groups == {'on_failure': [1, 2, 3]}
    pb.failure_append_step(4)
    assert pb.step_groups == {'on_failure': [1, 2, 3, 4]}


def test_pipeline_body_create_steps_group_and_append():
    """Create steps group and append to it."""
    pb = PipelineBody()
    pb.create_steps_group([1, 2, 3])
    assert pb.step_groups == {'steps': [1, 2, 3]}
    pb.steps_append_step(4)
    assert pb.step_groups == {'steps': [1, 2, 3, 4]}


def test_pipeline_body_reserved_step_group_raises():
    """Raise error when trying to run a reserved step group name."""
    pb = PipelineBody()
    with pytest.raises(PipelineDefinitionError) as err:
        pb.run_step_group('_meta', Context())

    assert str(err.value).startswith(
        "_meta is reserved. Use a different step-group name. The reserved "
        + "names are: {")
    # remaining output looks like {'_meta', 'context_parser'}. Not asserting
    # because no sort order on set to str convert.

# endregion PipelineBody
