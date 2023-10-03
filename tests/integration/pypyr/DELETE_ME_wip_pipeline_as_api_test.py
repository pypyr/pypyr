from pypyr.pipedef import PipelineBody
from pypyr.dsl import Step, RetryDecorator, PyString
from pypyr.pipelinerunner import run_pipeline_body

from pypyr.config import config
import pypyr.log.logger

# optional - one-time loading of config from files
config.init()

# initialize logging once
# use the same log format & level defaults as the cli
pypyr.log.logger.set_root_logger()

pipeline_body = PipelineBody()
pipeline_body.create_steps_group([
    Step(name='pypyr.steps.echo',
         in_parameters={'echoMe': "test 123"}),
    Step(name='pypyr.steps.echo',
         in_parameters={'echoMe': "test 456"})

])
run_pipeline_body(pipeline_name='test-pipe', pipeline_body=pipeline_body)

pipeline_body = PipelineBody()
pipeline_body.create_steps_group([
    Step(name='pypyr.steps.set',
         in_parameters={'set': {'a': 'b'}}),
    Step(name='pypyr.steps.echo',
         in_parameters={'echoMe': PyString("print('test 4567')")},
         retry_decorator=RetryDecorator(sleep=1, max=3))

])


pipeline_body.steps_append_step(
    Step(name='pypyr.steps.echo',
         in_parameters={'echoMe': "890"}))

pipeline_body.steps_append_step(
    Step(name='pypyr.steps.echo',
         in_parameters={'echoMe': "111213"}))

context = run_pipeline_body(
    pipeline_name='test-pipe', pipeline_body=pipeline_body)
print(context)
