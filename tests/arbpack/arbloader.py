"""Test custom loader which returns directly the same thing that was passed."""


def get_pipeline_definition(pipeline_name, working_dir):
    """Return inputs as a mock pipeline loader stub."""
    return {'pipeline_name': pipeline_name, 'working_dir': working_dir}
