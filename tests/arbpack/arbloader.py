"""Test custom loader which returns directly the same thing that was passed."""


def get_pipeline_definition(pipeline_name, parent):
    """Return inputs as a mock pipeline loader stub."""
    return {'pipeline_name': pipeline_name, 'parent': parent}
