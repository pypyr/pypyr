"""Naive file loader for integration testing."""
import pypyr.yaml


def get_pipeline_definition(pipeline_name, working_dir):
    """Simplified file loader for integration testing."""
    with open(working_dir.joinpath(f'{pipeline_name}.yaml')) as yaml_file:
        return pypyr.yaml.get_pipeline_yaml(yaml_file)
