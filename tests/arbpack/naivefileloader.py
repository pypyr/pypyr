"""Simple file loader for integration testing."""
from pathlib import Path
import pypyr.yaml


def get_pipeline_definition(pipeline_name, working_dir):
    """Simplified file loader for integration testing."""
    with open(Path(working_dir).joinpath(f'{pipeline_name}.yaml')
              ) as yaml_file:
        return pypyr.yaml.get_pipeline_yaml(yaml_file)
