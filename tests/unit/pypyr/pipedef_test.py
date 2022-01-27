"""pipedef.py unit tests."""
from pypyr.pipedef import PipelineDefinition, PipelineInfo, PipelineFileInfo

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
