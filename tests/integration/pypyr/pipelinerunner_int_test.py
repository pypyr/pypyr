"""pipelinerunner.py integration tests."""
import os
import pypyr.pipelinerunner
# ------------------------- integration---------------------------------------#


def test_pipeline_runner_main():
    """Smoke test for pipeline runner main.

    Strictly speaking this is an integration test, not a unit test.
    """
    working_dir = os.path.join(
        os.getcwd(),
        'tests')
    pypyr.pipelinerunner.main(pipeline_name='smoke',
                              pipeline_context_input=None,
                              working_dir=working_dir,
                              log_level=50,
                              log_path=None)
# ------------------------- integration---------------------------------------#
