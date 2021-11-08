"""PipelineDefinition and PipelineInfo classes.

A loader creates these. The PipelineDefinition holds the yaml payload of a
pipeline, and the PipelineInfo holds the pipeline metadata properties set by
the loader.

For the run-time arguments associated with a running pipeline, see
pypyr.pipeline.Pipeline instead.

All of the below could well be DataClasses + slots once py3.10 the min
supported version. Might be nice to have frozen class to make these hashable.
"""


class PipelineDefinition():
    """The pipeline body and its metadata.

    A loader creates the PipelineDefinition and sets the metadata in .info.

    The PipelineDefinition is a globally shared cache of the pipeline body &
    meta-data.

    Attributes:
        pipeline (dict-like): The pipeline yaml body.
        info (PipelineInfo): Meta-data set by the loader for the pipeline.
    """

    __slots__ = ['pipeline', 'info']

    def __init__(self, pipeline, info):
        """Initialize a pipeline definition.

        Args:
            pipeline (dict-like): The pipeline yaml body itself.
            info (PipelineInfo): Meta-data set by the loader for the pipeline.
        """
        self.pipeline = pipeline
        self.info = info

    def __eq__(self, other):
        """Equality comparison checks Pipeline and info objects are equal."""
        return (isinstance(other, type(self))
                and all(
                    getattr(self, s, object()) == getattr(other, s, object())
                    for s in self.__slots__))


class PipelineInfo():
    """The common attributes that every pipeline loader should set.

    Custom loaders that want to add more properties to a pipeline's meta-data
    should probably derive from this class.

    Attributes:
        pipeline_name (str): Name of pipeline, as set by the loader.
        loader (str): Absolute module name of the pipeline loader.
        parent (any): pipeline_name resolves from parent. The parent can be any
            type - it is up to the loader to interpret the parent property.
        is_loader_cascading (bool): Loader cascades to child pipelines if not
            otherwise set on pype. Default True.
        is_parent_cascading (bool): Parent cascades to child pipelines if not
            otherwise set on pype. Default True.
    """

    __slots__ = ['pipeline_name', 'loader', 'parent',
                 'is_loader_cascading', 'is_parent_cascading']

    def __init__(self, pipeline_name, loader, parent,
                 is_parent_cascading=True,
                 is_loader_cascading=True):
        """Initialize PipelineInfo.

        Args:
            pipeline_name (str): name of pipeline, as set by the loader.
            loader (str): absolute module name of pypeloader.
            parent (any): pipeline_name resolves from parent.
            is_loader_cascading (bool): Loader cascades to child pipelines if
                not otherwise set on pype. Default True.
            is_parent_cascading (bool): Parent cascades to child pipelines if
                not otherwise set on pype. Default True.
        """
        self.pipeline_name = pipeline_name
        self.loader = loader
        self.parent = parent
        self.is_loader_cascading = is_loader_cascading
        self.is_parent_cascading = is_parent_cascading

    def __eq__(self, other):
        """Check all instance attributes are equal."""
        return (isinstance(other, type(self))
                and all(
                    getattr(self, s, object()) == getattr(other, s, object())
            for s in self.__slots__))


class PipelineFileInfo(PipelineInfo):
    """Pipeline properties set by the default file loader.

    Loader and parent will cascade by default to child pipelines if not set
    otherwise on pypyr.steps.pype.

    Attributes:
        pipeline_name (str): Name of pipeline, as set by the loader.
        loader (str): Absolute module name of pypeloader.
        parent (Path): Path to the pipeline's parent directory on the
            file-system.
        path (Path): Path to the pipeline on the file system.
    """

    __slots__ = ['path']

    def __init__(self, pipeline_name, loader, parent, path):
        """Initialize PipelineFleInfo.

        Args:
            pipeline_name (str): name of pipeline, as set by the loader.
            loader (str): absolute module name of pypeloader.
            parent (Path): Path to the pipeline's parent directory on the
                file-system.
            path (Path): Path to the pipeline on the file system.
        """
        super().__init__(pipeline_name=pipeline_name,
                         loader=loader,
                         parent=parent)
        self.path = path
