"""Naive file loader for integration testing."""
from pathlib import Path
import pypyr.yaml

working_dir_tests = Path.cwd().joinpath('tests')


def get_pipeline_definition(pipeline_name, parent):
    """Simplified file loader for integration testing."""
    with open(working_dir_tests.joinpath(
            f'{pipeline_name}.yaml'), encoding='utf-8') as yaml_file:
        return pypyr.yaml.get_pipeline_yaml(yaml_file)
