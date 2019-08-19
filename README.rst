#########################
pypyr cli pipeline runner
#########################

.. image:: https://pypyr.io/images/pypyr-logo-small.png
    :alt: pypyr-logo
    :align: left

*pypyr*
    pronounce how you like, but I generally say *piper* as in "piping down the
    valleys wild"


pypyr is a command line interface to run pipelines defined in yaml. Think of
pypyr as a simple task runner that lets you define and run sequential steps.
Like a turbo-charged shell script, but less finicky.

You can run loops, conditionally execute steps based on conditions you specify,
wait for status changes before continuing, break on failure conditions or
swallow errors. Pretty useful for orchestrating continuous integration,
continuous deployment and devops operations.

Read, merge and write configuration files to and from yaml, json or just text.

|build-status| |coverage| |pypi|

.. contents::

.. section-numbering::

************
Installation
************

pip
===
.. code-block:: bash

  $ pip install --upgrade pypyr

python version
==============
Tested against Python >=3.6

docker
======
Stuck with an older version of python? Want to run pypyr in an environment that
you don't control, like a CI server somewhere?

You can use the official pypyr docker image as a drop-in replacement for the
pypyr executable. https://hub.docker.com/r/pypyr/pypyr/

.. code-block:: bash

  $ docker run pypyr/pypyr echo "Ceci n'est pas une pipe"


*****
Usage
*****
Run your first pipeline
=======================
Run one of the built-in pipelines to get a feel for it:

.. code-block:: bash

  $ pypyr echo "Ceci n'est pas une pipe"

You can achieve the same thing by running a pipeline where the context is set
in the pipeline yaml rather than passed in as the 2nd positional argument:

.. code-block:: bash

  $ pypyr magritte

Check here `pypyr.steps.echo`_ to see yaml that does this.

Run a pipeline
==============
pypyr runs the pipeline specified by the name that you pass to the cli.

To make your pipelines edit easier in your favorite yaml editor, use a .yaml
extension, but to save on typing you don't need to enter the .yaml bit at the
command line. You can use your usual directory separators if you're running
a pipeline in a sub-directory, like ``pypyr subdir/subsubdir/pipeline``

.. code-block:: bash

  # run ./mypipelinename.yaml with DEBUG logging level
  $ pypyr mypipelinename --loglevel 10

  # run ./mypipelinename.yaml with INFO logging level.
  # log is an alias for loglevel, so less typing, wooohoo!
  $ pypyr mypipelinename --log 20

  # If you don't specify --loglevel it defaults to 25 - NOTIFY logging level.
  $ pypyr mypipelinename

  # run ./mydir/mypipelinename.yaml
  # The 2nd argument is any arbitrary sequence of strings, known as the input
  # context arguments.
  # For this input argument to be available
  # to your pipeline you need to specify a context parser in your pipeline yaml.
  $ pypyr mydir/mypipelinename arbitrary string here

  # run ./mypipelinename.yaml with an input context in key-value
  # pair format. For this input to be available to your pipeline you need to
  # specify a context_parser like pypyr.parser.keyvaluepairs in your
  # pipeline yaml.
  $ pypyr mypipelinename mykey=value anotherkey=anothervalue


Get cli help
============
pypyr has a couple of arguments and switches you might find useful. See them all
here:

.. code-block:: bash

  $ pypyr -h

Examples
========
If you prefer reading code to reading words, https://github.com/pypyr/pypyr-example

*********************************************
Pipeline directory locations look-up sequence
*********************************************
pypyr looks for pipelines in a sequence where it searches different directories
in a specific order. pypyr runs the 1st pipeline it finds in the look-up
sequence.

Working dir is your current directory, unless you use the ``--dir`` flag to
tell pypyr something different.

Assuming you run ``pypyr pipeline-name``, this is the look-up sequence:

1. {working dir}/{pipeline-name}.yaml
2. {working dir}/pipelines/{pipeline-name}.yaml
3. {pypyr install directory}/pipelines/{pipeline-name}.yaml

The last look-up is for pypyr built-in pipelines. You probably shouldn't be
saving your own pipelines there, they might get over-written or wiped by
upgrades or re-installs.

***************************
Anatomy of a pypyr pipeline
***************************
Pipeline yaml structure
=======================
A pipeline is a .yaml file. pypyr uses YAML version 1.2.

Save pipelines wherever you please. To run a pipeline, execute
``pypyr pipelinename`` from the directory where you saved ``pipelinename.yaml``

.. code-block:: yaml

  # This is an example showing the anatomy of a pypyr pipeline
  # A pipeline should be saved as {working dir}/mypipelinename.yaml.
  # Run the pipeline from {working dir} like this: pypyr mypipelinename

  # optional
  context_parser: my.custom.parser

  # mandatory.
  steps:
    - my.package.my.module # simple step pointing at a python module in a package
    - mymodule # simple step pointing at a python file
    - name: my.package.another.module # complex step. It contains a description and in parameters.
      description: Optional description is for humans. It's any text that makes your life easier.
      in: # optional. In parameters are added to the context so that this step and subsequent steps can use these key-value pairs.
        parameter1: value1
        parameter2: value2
      run: True # optional. Runs this step if True, skips step if False. Defaults to True if not specified.
      skip: False # optional. Skips this step if True, runs step if False. Defaults to False if not specified.
      swallow: False # optional. Swallows any errors raised by the step. Defaults to False if not specified.

  # optional.
  on_success:
    - my.first.success.step
    - my.second.success.step

  # optional.
  on_failure:
    - my.failure.handler.step
    - my.failure.handler.notifier


Custom step groups
==================
pypyr looks for 3 different step groups on a default run:

- steps
- on_success
- on_failure

.. code-block:: yaml

  # the default pypyr step-groups
  steps: # 'steps' is the default step-group that runs
    - steps.step1 # will run ./steps/step1.py
    - arb.step2 # will run ./arb/step2.py

  on_success: # on_success executes when the pipeline completes successfully
    - success_step # will run ./success_step.py

  on_failure: # on_failure executes whenever pipeline processing hits an error
    - steps.failure_step # will run ./steps/failure_step.py

You don't have to stick to these default step-groups, though. You can specify
your own step-groups, or mix in your own step-groups with the defaults.

.. code-block:: yaml

  # ./step-groups-example.yaml
  sg1:
    - name: pypyr.steps.echo
      in:
        echoMe: sg1.1
    - name: pypyr.steps.echo
      in:
        echoMe: sg1.2
  sg2:
    - name: pypyr.steps.echo
      in:
        echoMe: sg2.1
    - name: pypyr.steps.echo
      in:
        echoMe: sg2.2
  sg3:
    - name: pypyr.steps.echo
      in:
        echoMe: sg3.1
    - name: pypyr.steps.echo
      in:
        echoMe: sg3.2
  sg4:
    - name: pypyr.steps.echo
      in:
        echoMe: sg4.1
    - name: pypyr.steps.echo
      in:
        echoMe: sg4.2

You can use the ``--groups`` switch to specify which groups you want to run and
in what order:

``pypyr step-groups-example --groups sg2 sg1 sg3``

If you don't specify ``--groups`` pypyr will just look for the standard
*steps* group as per usual. You can still call other step-groups from the
default *steps* group, so you could think of *steps* a bit like the ``main()``
entrypoint in traditional programming.

Control-of-Flow
---------------
You can control the flow of pypyr pipeline execution between step-groups with
the following handy steps:

- `pypyr.steps.call`_
- `pypyr.steps.jump`_
- `pypyr.steps.stopstepgroup`_
- `pypyr.steps.stoppipeline`_
- `pypyr.steps.stop`_

You can call other pipelines from within a pipeline with:

- `pypyr.steps.pype`_

On top of this, you can control which individual steps should run or not using
the conditional `Step decorators`_ :

- ``run``
- ``skip``

Looping happens on the step-level, using the following `Step decorators`_ :

- ``while``
- ``foreach``

You can set a ``while`` or ``foreach`` loop on any given step, including on a
`pypyr.steps.call`_ step or a `pypyr.steps.pype`_ step, which lets you call
another step-group or pipeline repeatedly in a loop.

Built-in pipelines
==================
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| **pipeline**                | **description**                                 | **how to run**                                                                      |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| donothing                   | Does what it says. Nothing.                     |``pypyr donothing``                                                                  |
|                             |                                                 |                                                                                     |
|                             |                                                 |                                                                                     |
|                             |                                                 |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| echo                        | Echos context value echoMe to output.           |``pypyr echo text goes here``                                                        |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyrversion                | Prints the python cli version number.           |``pypyr pypyrversion``                                                               |
|                             |                                                 |                                                                                     |
|                             |                                                 |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| magritte                    | Thoughts about pipes.                           |``pypyr magritte``                                                                   |
|                             |                                                 |                                                                                     |
|                             |                                                 |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+

context_parser
==============
Optional.

A context_parser parses the pypyr command's context input arguments. This is
all the positional arguments after the pipeline-name from the command line.

The chances are pretty good that the context_parser will take the context
command arguments and put in into the pypyr context.

The pypyr context is a dictionary that is in scope for the duration of the entire
pipeline. The context_parser can initialize the context. Any step in the pipeline
can add, edit or remove items from the context dictionary.

Built-in context parsers
------------------------
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| **context parser**          | **description**                                 | **example input**                                                                   |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.dict           | Takes a key=value pair string and returns a     |``pypyr pipelinename param1=value1 param2="value 2" param3=value3``                  |
|                             | dictionary where each pair becomes a dictionary |                                                                                     |
|                             | element inside a dict with name *argDict*.      |This will create a context dictionary like this:                                     |
|                             |                                                 |                                                                                     |
|                             | Escape literal spaces with single or double     |.. code-block:: python                                                               |
|                             | quotes.                                         |                                                                                     |
|                             |                                                 |  {'argDict': {'param1': 'value1',                                                   |
|                             |                                                 |               'param2': 'value 2',                                                  |
|                             |                                                 |               'param3': 'value3'}}                                                  |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.json           | Takes a json string and returns a dictionary.   |``pypyr pipelinename {"key1":"value1","key2":"value2"}``                             |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.jsonfile       | Opens json file and returns a dictionary.       |``pypyr pipelinename "./path/sample.json"``                                          |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.keys           | For each input argument, create a dictionary    |``pypyr pipelinename param1 'par am2' param3``                                       |
|                             | where each element becomes the key, with value  |                                                                                     |
|                             | set to true.                                    |This will create a context dictionary like this:                                     |
|                             |                                                 |                                                                                     |
|                             | Escape literal spaces with single or double     |.. code-block:: python                                                               |
|                             | quotes.                                         |                                                                                     |
|                             |                                                 |  {'param1': True, 'par am2': True, 'param3': True}                                  |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.keyvaluepairs  | Takes a key=value pair string and returns a     |``pypyr pipelinename param1=value1 param2=value2 "param 3"=value3``                  |
|                             | dictionary where each pair becomes a dictionary |                                                                                     |
|                             | element.                                        |This will create a context dictionary like this:                                     |
|                             |                                                 |                                                                                     |
|                             | Escape literal spaces with single or double     |.. code-block:: python                                                               |
|                             | quotes.                                         |                                                                                     |
|                             |                                                 | {'param1': 'value1',                                                                |
|                             |                                                 |  'param2': 'value2',                                                                |
|                             |                                                 |  'param 3': 'value3'}                                                               |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.list           | Takes the input arguments and returns a list in |``pypyr pipelinename param1 param2 param3``                                          |
|                             | context with name *argList*.                    |                                                                                     |
|                             |                                                 |This will create a context dictionary like this:                                     |
|                             | Escape literal spaces with single or double     |                                                                                     |
|                             | quotes.                                         |.. code-block:: python                                                               |
|                             |                                                 |                                                                                     |
|                             |                                                 | {'argList': ['param1', 'param2', 'param3']}                                         |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.string         | Takes any arbitrary input and returns a single  |``pypyr pipelinename arbitrary string here``                                         |
|                             | string in context with name *argString*.        |                                                                                     |
|                             |                                                 |This will create a context dictionary like this:                                     |
|                             |                                                 |                                                                                     |
|                             |                                                 |.. code-block:: python                                                               |
|                             |                                                 |                                                                                     |
|                             |                                                 |  {'argString': 'arbitrary string here'}                                             |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.yamlfile       | Opens a yaml file and writes the contents into  |``pypyr pipelinename ./path/sample.yaml``                                            |
|                             | the pypyr context dictionary.                   |                                                                                     |
|                             |                                                 |                                                                                     |
|                             | The top (or root) level yaml should describe a  |                                                                                     |
|                             | map, not a sequence.                            |                                                                                     |
|                             |                                                 |                                                                                     |
|                             | Sequence (this won't work):                     |                                                                                     |
|                             |                                                 |                                                                                     |
|                             | .. code-block:: yaml                            |                                                                                     |
|                             |                                                 |                                                                                     |
|                             |   - thing1                                      |                                                                                     |
|                             |   - thing2                                      |                                                                                     |
|                             |                                                 |                                                                                     |
|                             | Instead, do a map (aka dictionary):             |                                                                                     |
|                             |                                                 |                                                                                     |
|                             | .. code-block:: yaml                            |                                                                                     |
|                             |                                                 |                                                                                     |
|                             |   thing1: thing1value                           |                                                                                     |
|                             |   thing2: thing2value                           |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+


Roll your own context_parser
----------------------------
.. code-block:: python

  import logging


  # getLogger will grab the parent logger context, so your loglevel and
  # formatting will inherit correctly automatically from the pypyr core.
  logger = logging.getLogger(__name__)


  def get_parsed_context(args):
      """This is the signature for a context parser.

      Args:
        args: list of string. Passed from command-line invocation where
              pypyr pipelinename this is the context_arg
              This would result in args == ['this', 'is', 'the', 'context_arg']

      Returns:
        dict. This dict will initialize the context for the pipeline run.
      """
      assert args, ("pipeline must be invoked with context arg set.")
      logger.debug("starting")

      # your clever code here. Chances are pretty good you'll be doing things
      # with the input args list to create a dictionary.

      # function signature returns a dictionary
      return {'key1': 'value1', 'key2':'value2'}

steps
=====
Mandatory.

steps is a list of steps to execute in sequence. A step is simply a bit of
python that does stuff.

You can specify a step in the pipeline yaml in two ways:

* Simple step

  - a simple step is just the name of the python module.

  - pypyr will look in your working directory for these modules or packages.

  - For a package, be sure to specify the full namespace (i.e not just `mymodule`, but `mypackage.mymodule`).

    .. code-block:: yaml

      steps:
        - my.package.my.module # points at a python module in a package.
        - mymodule # simple step pointing at a python file

* Complex step

  - a complex step allows you to specify a few more details for your step, but at heart it's the same thing as a simple step - it points at some python.

    .. code-block:: yaml

      steps:
        - name: my.package.another.module
          description: Optional Description is for humans.
                       It is any yaml-escaped text that makes your life easier.
                       Outputs to the console during runtime as INFO.
          comment: Optional comments for pipeline developers.
                   Does not output to console during run-time.
          in: #optional. In parameters are added to the context so that this step and subsequent steps can use these key-value pairs.
            parameter1: value1
            parameter2: value2


* You can freely mix and match simple and complex steps in the same pipeline.

* Frankly, the only reason simple steps are there is because I'm lazy and I dislike redundant typing.

Step decorators
---------------
Decorators overview
^^^^^^^^^^^^^^^^^^^
Complex steps have various optional step decorators that change how or if a step is run.

Don't bother specifying these unless you want to deviate from the default values.


.. code-block:: yaml

  steps:
    - name: my.package.another.module
      description: Optional Description is for humans.
                   Any yaml-escaped text that makes your life easier.
                   Outputs to console during run-time.
      comment: Optional comments for pipeline developers. Like code comments.
               Does not output to console during run.
      in: # optional. In parameters are added to the context.
          # this step and subsequent steps can use these key-value pairs.
        parameter1: value1
        parameter2: value2
      foreach: [] # optional. Repeat the step once for each item in this list.
      onError: # optional. Custom Error Info to add to error if step fails.
        code: 111 # you can also use custom elements for your custom error.
        description: arb description here
      retry: # optional. Retry step until it doesn't raise an error.
        max: 1 # max times to retry. integer. Defaults None (infinite).
        sleep: 0 # sleep between retries, in seconds. Decimals allowed. Defaults 0.
        stopOn: ['ValueError', 'MyModule.SevereError'] # Stop retry on these errors. Defaults None (retry all).
        retryOn: ['TimeoutError'] # Only retry these errors. Defaults None (retry all).
      run: True # optional. Runs this step if True, skips step if False. Defaults to True if not specified.
      skip: False # optional. Skips this step if True, runs step if False. Defaults to False if not specified.
      swallow: False # optional. Swallows any errors raised by the step. Defaults to False if not specified.
      while: # optional. repeat step until stop is True or max iterations reached.
        stop: '{keyhere}' # loop until this evaluates True.
        max: 1 # max loop iterations to run. integer. Defaults None (infinite).
        sleep: 0 # sleep between iterations, in seconds. Decimals allowed. Defaults 0.
        errorOnMax: False # raise error if max reached. Defaults False.

+---------------+----------+---------------------------------------------+----------------+
| **decorator** | **type** | **description**                             | **default**    |
+---------------+----------+---------------------------------------------+----------------+
| foreach       | list     | Run the step once for each item in the list.| None           |
|               |          | The iterator is ``context['i']``.           |                |
|               |          |                                             |                |
|               |          | The *run*, *skip* & *swallow* decorators    |                |
|               |          | evaluate dynamically on each iteration.     |                |
|               |          | So if during an iteration the step's logic  |                |
|               |          | sets ``run=False``, the step will not       |                |
|               |          | execute on the next iteration.              |                |
+---------------+----------+---------------------------------------------+----------------+
| in            | dict     | Add this to the context so that this        | None           |
|               |          | step and subsequent steps can use these     |                |
|               |          | key-value pairs.                            |                |
|               |          |                                             |                |
|               |          | *in* evaluates once at the beginning of step|                |
|               |          | execution, before the *foreach* and *while* |                |
|               |          | decorators. It does not re-evaluate for each|                |
|               |          | loop iteration.                             |                |
+---------------+----------+---------------------------------------------+----------------+
| onError       | any      | If this  step errors, write the contents of | None           |
|               |          | *onError* to *runErrors.customError* in     |                |
|               |          | context. Subsequent steps can then use this |                |
|               |          | information, assuming you've got a *swallow*|                |
|               |          | somewhere in the call chain.                |                |
|               |          |                                             |                |
|               |          | *onError* can be a simple string, or your   |                |
|               |          | your own dict, or any given object. You can |                |
|               |          | use `Substitutions`_.                       |                |
+---------------+----------+---------------------------------------------+----------------+
| retry         | dict     | Retries the step until it doesn't error.    | None           |
|               |          | The retry iteration counter is              |                |
|               |          | ``context['retryCounter']``.                |                |
|               |          |                                             |                |
|               |          | If you reach *max* while the step still     |                |
|               |          | errors, will raise the last error and stop  |                |
|               |          | further pipeline processing, unless         |                |
|               |          | *swallow* is True.                          |                |
|               |          |                                             |                |
|               |          | When neither *stopOn* and *retryOn* set,    |                |
|               |          | all types of errors will retry.             |                |
|               |          |                                             |                |
|               |          | If *stopOn* is specified, errors listed     |                |
|               |          | in *stopOn* will stop retry processing and  |                |
|               |          | raise an error. Errors not listed in        |                |
|               |          | *stopOn* will retry.                        |                |
|               |          |                                             |                |
|               |          | If *retryOn* is specified, ONLY errors      |                |
|               |          | listed in *retryOn* will retry.             |                |
|               |          |                                             |                |
|               |          | *max* evaluates before *stopOn* and         |                |
|               |          | *retryOn*. *stopOn* supersedes *retryOn*.   |                |
|               |          |                                             |                |
|               |          | For builtin python errors, specify the bare |                |
|               |          | error name for *stopOn* and *retryOn*, e.g  |                |
|               |          | 'ValueError', 'KeyError'.                   |                |
|               |          |                                             |                |
|               |          | For all other errors, use module.errorname, |                |
|               |          | e.g 'mypackage.mymodule.myerror'            |                |
+---------------+----------+---------------------------------------------+----------------+
| run           | bool     | Runs this step if True, skips step if       | True           |
|               |          | False.                                      |                |
+---------------+----------+---------------------------------------------+----------------+
| skip          | bool     | Skips this step if True, runs step if       | False          |
|               |          | False. Evaluates after the *run* decorator. |                |
|               |          |                                             |                |
|               |          | If this looks like it's merely the inverse  |                |
|               |          | of *run*, that's because it is. Use         |                |
|               |          | whichever suits your pipeline better, or    |                |
|               |          | combine *run* and *skip* in the same        |                |
|               |          | pipeline to toggle at runtime which steps   |                |
|               |          | you want to execute.                        |                |
+---------------+----------+---------------------------------------------+----------------+
| swallow       | bool     | If True, ignore any errors raised by the    | False          |
|               |          | step and continue to the next step.         |                |
|               |          | pypyr logs the error, so you'll know what   |                |
|               |          | happened, but processing continues.         |                |
+---------------+----------+---------------------------------------------+----------------+
| while         | dict     | Repeat step until *stop* is True, or until  | None           |
|               |          | *max* iterations reached. You have to       |                |
|               |          | specify either *max* or *stop*. The loop    |                |
|               |          | position counter is                         |                |
|               |          | ``context['whileCounter']``                 |                |
|               |          |                                             |                |
|               |          | If you specify both *max* and *stop*, the   |                |
|               |          | loop exits when *stop* is True as long as   |                |
|               |          | it's still under *max* iterations. *max*    |                |
|               |          | will exit the loop even if *stop* is still  |                |
|               |          | False. If you want to error and stop        |                |
|               |          | processing when *max* exhausts (maybe you   |                |
|               |          | are waiting for *stop* to reach True but    |                |
|               |          | want to timeout after *max*) set            |                |
|               |          | *errorOnMax* to True.                       |                |
+---------------+----------+---------------------------------------------+----------------+

All step decorators support `Substitutions`_. You can use `py strings`_ for
dynamic boolean conditions like ``len(key) > 0``.

If no looping decorators are specified, the step will execute once (depending
on the conditional decorators' settings).

If all of this sounds complicated, don't panic! If you don't bother with any of
these the step will just run once by default.

decorator bool evaluation
^^^^^^^^^^^^^^^^^^^^^^^^^
Note that for all bool values, the standard Python truth value testing rules apply.
https://docs.python.org/3/library/stdtypes.html#truth-value-testing

Simply put, this means that 1, TRUE, True and true will be True.

None/Empty, 0,'', [], {} will be False.

Decorator order of precedence
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Decorators can interplay, meaning that the sequence of evaluation is important.

- *run* or *skip* controls whether a step should execute on any
  given loop iteration, without affecting continued loop iteration.

- *run* could be True but *skip* True will still skip the step.

- A step can run multiple times in a *foreach* loop for each iteration of a
  *while* loop.

- *swallow* can evaluate dynamically inside a loop to decide whether to swallow
  an error or not on a particular iteration.

- *swallow* can swallow an error after *retry* exhausted max attempts.

.. code-block:: yaml

  in # in evals once and only once at the beginning of step
    -> while # everything below loops inside while
      -> foreach # everything below loops inside foreach
        -> run # evals dynamically on each loop iteration
         -> skip # evals dynamically on each loop iteration after run
          -> retry # repeats step execution until no error
            [>>>actual step execution here<<<]
          -> swallow # evaluated dynamically on each loop iteration

Decorator examples
^^^^^^^^^^^^^^^^^^
+------------------------------------------------+-----------------------------+
| **example**                                    | **link**                    |
+------------------------------------------------+-----------------------------+
| conditional step decorators                    | |step-decorators|           |
+------------------------------------------------+-----------------------------+
| dynamic expression evaluation                  | |pystring-decorator|        |
+------------------------------------------------+-----------------------------+
| foreach looping                                | |foreach-decorator|         |
+------------------------------------------------+-----------------------------+
| foreach with dynamic conditional decorator     | |foreach-dynamic|           |
| evaluation.                                    |                             |
+------------------------------------------------+-----------------------------+
| retry                                          | |retry-decorator|           |
+------------------------------------------------+-----------------------------+
| retry with retryOn                             | |retry-decorator-retryon|   |
+------------------------------------------------+-----------------------------+
| retry with stopOn                              | |retry-decorator-stopon|    |
+------------------------------------------------+-----------------------------+
| while looping                                  | |while-decorator|           |
+------------------------------------------------+-----------------------------+
| while with sleep intervals                     | |while-sleep|               |
+------------------------------------------------+-----------------------------+
| while combined with foreach                    | |while-foreach|             |
+------------------------------------------------+-----------------------------+
| while with error on reaching max or never      | |while-exhaust|             |
| reaching a stop condition.                     |                             |
+------------------------------------------------+-----------------------------+
| while loop that runs infinitely                | |while-infinite|            |
+------------------------------------------------+-----------------------------+

.. |step-decorators| replace:: `step decorators <https://github.com/pypyr/pypyr-example/blob/master/pipelines/stepdecorators.yaml>`__

.. |pystring-decorator| replace:: `dynamic expression <https://github.com/pypyr/pypyr-example/blob/master/pipelines/pystrings.yaml>`__

.. |foreach-decorator| replace:: `foreach <https://github.com/pypyr/pypyr-example/blob/master/pipelines/foreach.yaml>`__

.. |foreach-dynamic| replace:: `foreach dynamic conditionals <https://github.com/pypyr/pypyr-example/blob/master/pipelines/foreachconditionals.yaml>`__

.. |retry-decorator| replace:: `retry decorator <https://github.com/pypyr/pypyr-example/blob/master/pipelines/retry.yaml>`__

.. |retry-decorator-retryon| replace:: `retry decorator retryOn <https://github.com/pypyr/pypyr-example/blob/master/pipelines/retryontypes.yaml>`__

.. |retry-decorator-stopon| replace:: `retry decorator stopOn <https://github.com/pypyr/pypyr-example/blob/master/pipelines/retrystopon.yaml>`__

.. |while-decorator| replace:: `while decorator <https://github.com/pypyr/pypyr-example/blob/master/pipelines/while.yaml>`__

.. |while-sleep| replace:: `while with sleep <https://github.com/pypyr/pypyr-example/blob/master/pipelines/while-sleep.yaml>`__

.. |while-foreach| replace:: `while foreach <https://github.com/pypyr/pypyr-example/blob/master/pipelines/while-foreach.yaml>`__

.. |while-exhaust| replace:: `while exhaust <https://github.com/pypyr/pypyr-example/blob/master/pipelines/while-exhaust.yaml>`__

.. |while-infinite| replace:: `while infinite <https://github.com/pypyr/pypyr-example/blob/master/pipelines/while-infinite.yaml>`__

Built-in steps
--------------

+-------------------------------+-------------------------------------------------+------------------------------+
| **step**                      | **description**                                 | **input context properties** |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.assert`_         | Stop pipeline if item in context is not as      | assert (dict)                |
|                               | expected.                                       |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.call`_           | Call another step-group. Continue with current  | call (dict or str)           |
|                               | execution after the called groups are done.     |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.cmd`_            | Runs the program and args specified in the      | cmd (string or dict)         |
|                               | context value ``cmd`` as a subprocess.          |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.contextclear`_   | Remove specified items from context.            | contextClear (list)          |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.contextclearall`_| Wipe the entire context.                        |                              |
|                               |                                                 |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.contextmerge`_   | Merges values into context, preserving the      | contextMerge (dict)          |
|                               | existing context hierarchy.                     |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.contextset`_     | Set context values from already existing        | contextSet (dict)            |
|                               | context values.                                 |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.contextsetf`_    | Set context keys from formatting                | contextSetf (dict)           |
|                               | expressions with {token} substitutions.         |                              |
|                               |                                                 |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.debug`_          | Pretty print pypyr context to output.           | debug (dict)                 |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.default`_        | Set default values in context. Only set values  | defaults (dict)              |
|                               | if they do not exist already.                   |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.echo`_           | Echo the context value ``echoMe`` to the output.| echoMe (string)              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.env`_            | Get, set or unset $ENVs.                        | env (dict)                   |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.envget`_         | Get $ENVs and use a default if they don't exist.| envget (list)                |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.fetchjson`_      | Loads json file into pypyr context.             | fetchJson (dict)             |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.fetchyaml`_      | Loads yaml file into pypyr context.             | fetchYaml (dict)             |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.fileformat`_     | Parse file and substitute {tokens} from         | fileFormat (dict)            |
|                               | context.                                        |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.fileformatjson`_ | Parse json file and substitute {tokens} from    | fileFormatJson (dict)        |
|                               | context.                                        |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.fileformatyaml`_ | Parse yaml file and substitute {tokens} from    | fileFormatYaml (dict)        |
|                               | context.                                        |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.filereplace`_    | Parse input file and replace search strings.    | fileReplace (dict)           |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.filewritejson`_  | Write payload to file in json format.           | fileWriteJson (dict)         |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.filewriteyaml`_  | Write payload to file in yaml format.           | fileWriteYaml (dict)         |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.glob`_           | Get paths from glob expression.                 | glob (string or list)        |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.jump`_           | Jump to another step-group. This means the rest | jump (dict or str)           |
|                               | of the current step-group doesn't run.          |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.pathcheck`_      | Check if path exists on filesystem.             | pathCheck (string or dict)   |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.py`_             | Executes the context value ``pycode`` as python | pycode (string)              |
|                               | code.                                           |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.pype`_           | Run another pipeline from within the current    | pype (dict)                  |
|                               | pipeline.                                       |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.pypyrversion`_   | Writes installed pypyr version to output.       |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.now`_            | Saves current local date/time to context        | nowIn (str)                  |
|                               | ``now``.                                        |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.nowutc`_         | Saves current utc date/time to context          | nowUtcIn (str)               |
|                               | ``nowUtc``.                                     |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.safeshell`_      | Alias for `pypyr.steps.cmd`_.                   | cmd (string or dict)         |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.shell`_          | Runs the context value ``cmd`` in the default   | cmd (string or dict)         |
|                               | shell. Use for pipes, wildcards, $ENVs, ~       |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.stop`_           | Stop pypyr entirely.                            |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.stoppipeline`_   | Stop current pipeline.                          |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.stopstepgroup`_  | Stop current step-group.                        |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.tar`_            | Archive and/or extract tars with or without     | tar (dict)                   |
|                               | compression. Supports gzip, bzip2, lzma.        |                              |
|                               |                                                 |                              |
+-------------------------------+-------------------------------------------------+------------------------------+

pypyr.steps.assert
^^^^^^^^^^^^^^^^^^
Assert that something is True or equal to something else.

Uses these context keys:

- ``assert``

  - ``this``

    - mandatory
    - If assert['equals'] not specified, evaluates as a boolean.

  - ``equals``

    - optional
    - If specified, compares ``assert['this']`` to ``assert['equals']``

If ``assert['this']`` evaluates to False raises error.

If ``assert['equals']`` is specified, raises error if
``assert['this'] != assert['equals']``.

Supports `Substitutions`_.

Examples:

.. code-block:: yaml

    assert: # continue pipeline
      this: True
    assert: # stop pipeline
      this: False

or with substitutions:

.. code-block:: yaml

    interestingValue: True
    assert:
      this: '{interestingValue}' # continue with pipeline

Non-0 numbers evalute to True:

.. code-block:: yaml

    assert:
      this: 1 # non-0 numbers assert to True. continue with pipeline

String equality:

.. code-block:: yaml

    assert:
      this: 'up the valleys wild'
      equals: 'down the valleys wild' # strings not equal. stop pipeline.

String equality with substitutions:

.. code-block:: yaml

    k1: 'down'
    k2: 'down'
    assert:
      this: '{k1} the valleys wild'
      equals: '{k2} the valleys wild' # substituted strings equal. continue pipeline.


Number equality:

.. code-block:: yaml

    assert:
      this: 123.45
      equals: 0123.450 # numbers equal. continue with pipeline.

Number equality with substitutions:

.. code-block:: yaml

    numberOne: 123.45
    numberTwo: 678.9
    assert:
      this: '{numberOne}'
      equals: '{numberTwo}' # substituted numbers not equal. Stop pipeline.

Complex types:

.. code-block:: yaml

  complexOne:
    - thing1
    - k1: value1
      k2: value2
      k3:
        - sub list 1
        - sub list 2
  complexTwo:
    - thing1
    - k1: value1
      k2: value2
      k3:
        - sub list 1
        - sub list 2
  assert:
    this: '{complexOne}'
    equals: '{complexTwo}' # substituted types equal. Continue pipeline.


See a worked example `for assert here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/assert.yaml>`__.

pypyr.steps.call
^^^^^^^^^^^^^^^^
Call another step-group. Once the called group(s) are complete, continues
processing from the point where you called.

If you want to jump to a different step-group and ignore the rest of the
step-group you're in, use `pypyr.steps.jump`_ instead.

*call* expects a context item *call*. It can take one of two forms:

.. code-block:: yaml

  - name: pypyr.steps.call
    comment: simple string means just call the step-group named "callme"
    in:
      call: callme
  - name: pypyr.steps.call
    comment: specify groups, success and failure.
    in:
      call:
        groups: ['callme', 'noreally'] # list. Step-groups to call.
        success: group_to_call_on_success # string. Single step-group name.
        failure: group_to_call_on_failure # string. Single step-group name.

*call.groups* can be a simple string if you're just calling a single group -
i.e you don't need to make it a list of one item.

Call can be handy if you use it in conjunction with looping step decorators
like *while* or *foreach*:

.. code-block:: yaml

  steps:
    - name: pypyr.steps.echo
      in:
        echoMe: this is the 1st step of steps
    - name: pypyr.steps.call
      in:
        call: arbgroup
    - name: pypyr.steps.echo
      in:
       echoMe: You'll see me AFTER arbgroup is done.
    - name: pypyr.steps.call
      foreach: ['one', 'two', 'three']
      in:
        call: repeatme
  arbgroup:
      - name: pypyr.steps.echo
        in:
          echoMe: this is arb group
      - pypyr.steps.stopstepgroup
      - name: pypyr.steps.echo
        in:
          echoMe: if you see me something is WRONG.
  repeatme:
      - name: pypyr.steps.echo
        in:
          echoMe: this is iteration {i}


This will result in:

.. code-block:: text

  NOTIFY:pypyr.steps.echo:run_step: this is the 1st step of steps
  NOTIFY:pypyr.steps.echo:run_step: this is arb group
  NOTIFY:pypyr.steps.echo:run_step: You'll see me AFTER arbgroup is done.
  NOTIFY:pypyr.steps.echo:run_step: this is iteration one
  NOTIFY:pypyr.steps.echo:run_step: this is iteration two
  NOTIFY:pypyr.steps.echo:run_step: this is iteration three


Call only runs success or failure groups if you actually specify these.

All inputs support string `Substitutions`_.

See a worked example for `call here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/call.yaml>`__.

pypyr.steps.cmd
^^^^^^^^^^^^^^^
Runs the context value *cmd* as a sub-process.

In *cmd*, you cannot use things like exit, return, shell pipes, filename
wildcards, environment variable expansion, and expansion of ~ to a user’s
home directory. Use `pypyr.steps.shell`_ for this instead. *cmd* runs a
program, it does not invoke the shell.

Input context can take one of two forms:

.. code-block:: yaml

  - name: pypyr.steps.cmd
    description: passing cmd as a string does not save the output to context.
                 it prints stdout in real-time.
    in:
      cmd: 'echo ${PWD}'
  - name: pypyr.steps.cmd
    description: passing cmd as a dict allows you to specify if you want to
                 save the output to context.
                 it prints command output only AFTER it has finished running.
    in:
      cmd:
        run: 'echo ${PWD}'
        save: True
        cwd: './current/working/dir/here'

If ``cwd`` is specified, will change the current working directory to *cwd* to
execute this command. The directory change is only for the duration of this
step, not any subsequent steps. If *cwd* is specified, the executable or program
specified in *run* is relative to the *cwd* if the *run* cmd uses relative paths.

If ``cwd`` is not specified, defaults to the current working directory, which
is from wherever you are running ``pypyr``.

Be aware that if *save* is True, all of the command output ends up in memory.
Don't specify it unless your pipeline uses the stdout/stderr response in
subsequent steps. Keep in mind that if the invoked command return code returns
a non-zero return code pypyr will automatically raise a *CalledProcessError*
and stop the pipeline.

If *save* is True, pypyr will save the output to context as follows:

.. code-block:: yaml

    cmdOut:
        returncode: 0
        stdout: 'stdout str here. None if empty.'
        stderr: 'stderr str here. None if empty.'

*cmdOut.returncode* is the exit status of the called process. Typically 0 means
OK. A negative value -N indicates that the child was terminated by signal N
(POSIX only).

You can use cmdOut in subsequent steps like this:

.. code-block:: yaml

  - name: pypyr.steps.echo
    run: !py "cmdOut['returncode'] == 0"
    in:
      echoMe: "you'll only see me if cmd ran successfully with return code 0.
              the command output was: {cmdOut[stdout]}"

Supports string `Substitutions`_.

Example pipeline yaml:

.. code-block:: bash

  steps:
    - name: pypyr.steps.cmd
      in:
        cmd: ls -a

See a worked example `for cmd here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/shell.yaml>`__.

pypyr.steps.contextclear
^^^^^^^^^^^^^^^^^^^^^^^^
Remove the specified items from the context.

Will iterate ``contextClear`` and remove those keys from context.

For example, say input context is:

.. code-block:: yaml

    key1: value1
    key2: value2
    key3: value3
    key4: value4
    contextClear:
        - key2
        - key4
        - contextClear

This will result in return context:

.. code-block:: yaml

    key1: value1
    key3: value3

Notice how contextClear also cleared itself in this example.

pypyr.steps.contextclearall
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Wipe the entire context. No input context arguments required.

You can always use *contextclearall* as a simple step. Sample pipeline yaml:

.. code-block:: yaml

    steps:
      - my.arb.step
      - pypyr.steps.contextclearall
      - another.arb.step


pypyr.steps.contextmerge
^^^^^^^^^^^^^^^^^^^^^^^^
Merges values into context, preserving the existing hierarchy while only
updating the differing values as specified in the contextmerge input.

By comparison, *contextset* and *contextsetf* overwrite the destination
hierarchy that is in context already,

This step merges the contents of the context key *contextMerge* into context.
The contents of the *contextMerge* key must be a dictionary.

For example, say input context is:

.. code-block:: yaml

    key1: value1
    key2: value2
    key3:
        k31: value31
        k32: value32
    contextMerge:
        key2: 'aaa_{key1}_zzz'
        key3:
            k33: value33_{key1}
        key4: 'bbb_{key2}_yyy'

This will result in return context:

.. code-block:: yaml

    key1: value1
    key2: aaa_value1_zzz
    key3:
        k31: value31
        k32: value32
        k33: value33_value1
    key4: bbb_aaa_value1_zzz_yyy

List, Set and Tuple merging is purely additive, with no checks for uniqueness
or already existing list items. E.g context `[0,1,2]` with
contextMerge `[2,3,4]` will result in `[0,1,2,2,3,4]`.

Keep this in mind especially where complex types like dicts nest inside a list
- a merge will always add a new dict list item, not merge it into whatever dicts
might exist on the list already.

See a worked example for `contextmerge here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/contextmerge.yaml>`__.

pypyr.steps.contextset
^^^^^^^^^^^^^^^^^^^^^^
Sets context values from already existing context values.

This is handy if you need to prepare certain keys in context where a next step
might need a specific key. If you already have the value in context, you can
create a new key (or update existing key) with that value.

*contextset* and *contextsetf* overwrite existing keys. If you want to merge
new values into an existing destination hierarchy, use
`pypyr.steps.contextmerge`_ instead.

So let's say you already have `context['currentKey'] = 'eggs'`.
If you run newKey: currentKey, you'll end up with `context['newKey'] == 'eggs'`

For example, say your context looks like this,

.. code-block:: yaml

      key1: value1
      key2: value2
      key3: value3

and your pipeline yaml looks like this:

.. code-block:: yaml

  steps:
    - name: pypyr.steps.contextset
      in:
        contextSet:
          key2: key1
          key4: key3

This will result in context like this:

.. code-block:: yaml

    key1: value1
    key2: value1
    key3: value3
    key4: value3

See a worked example `for contextset here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/contextset.yaml>`__.

pypyr.steps.contextsetf
^^^^^^^^^^^^^^^^^^^^^^^
Set context keys from formatting expressions with `Substitutions`_.

Requires the following context:

.. code-block:: yaml

  contextSetf:
    newkey: '{format expression}'
    newkey2: '{format expression}'

*contextset* and *contextsetf* overwrite existing keys. If you want to merge
new values into an existing destination hierarchy, use
`pypyr.steps.contextmerge`_ instead.

For example, say your context looks like this:

.. code-block:: yaml

      key1: value1
      key2: value2
      answer: 42

and your pipeline yaml looks like this:

.. code-block:: yaml

  steps:
    - name: pypyr.steps.contextsetf
      in:
        contextSetf:
          key2: any old value without a substitution - it will be a string now.
          key4: 'What do you get when you multiply six by nine? {answer}'

This will result in context like this:

.. code-block:: yaml

    key1: value1
    key2: any old value without a substitution - it will be a string now.
    answer: 42
    key4: 'What do you get when you multiply six by nine? 42'

You can use *contextsetf* in conjunction with `py strings`_ for conditional
assignment of context items or ternary expressions.

.. code-block:: yaml

    arb1: null
    arb2: ''
    arb3: eggy
    arb4: [1,1,2,3,5,8]
    contextSetf:
      isNull: !py arb1 is None # make a bool based on None
      isEmpty: !py bool(arb2) # use truthy, empty strings are false
      ternaryResult: !py "'eggs' if arb3 == 'eggy' else 'ham'"
      isIn: !py 10 in arb4 # bool if thing in list

See a worked example `for contextsetf here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/contextset.yaml>`__.

pypyr.steps.debug
^^^^^^^^^^^^^^^^^
Pretty print the context to output.

Print the pypyr context to the pypyr output. This is likely to be the console.
This may assist in debugging when trying to see what values are what.

debug prints to the INFO (20) log-level. This means you won't see debug output
unless you specify ``pypyr mypype --log 20`` or lower.

Obviously, be aware that if you have sensitive values like passwords in your
context you probably want to be careful about this. No duh.

All inputs are optional. This means you can run debug in a pipeline as a
simple step just with

.. code-block:: yaml

    steps:
      - name: my.arb.step
        in:
          arb: arb1
      - pypyr.steps.debug # use debug as a simple step, with no config
      - name: another.arb.step
        in:
          another: value

In this case it will dump the entire context as is without applying formatting.

Debug supports the following optional inputs:

.. code-block:: yaml

    debug: # optional
      keys: keytodump # optional. str for a single key name to print.
                      # or a list of key names to print ['key1', 'key2'].
                      # if not specified, print entire context.
      format: False # optional. Boolean, defaults False.
                    # Applies formatting expressions to output.

See some worked examples of `use debug to pretty print context here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/debug.yaml>`__.

pypyr.steps.default
^^^^^^^^^^^^^^^^^^^
Sets values in context if they do not exist already. Does not overwrite
existing values. Supports nested hierarchies.

This is especially useful for setting default values in context, for example
when using `optional arguments
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/defaultarg.yaml>`__.
from the shell.

This step sets the contents of the context key *defaults* into context where
keys in *defaults* do not exist in context already.
The contents of the *defaults* key must be a dictionary.

Example:
Given a context like this:

.. code-block:: yaml

    key1: value1
    key2:
        key2.1: value2.1
    key3: None

And *defaults* input like this:

.. code-block:: yaml

    key1: updated value here won't overwrite since it already exists
    key2:
        key2.2: value2.2
    key3: key 3 exists so I won't overwrite

Will result in context:

.. code-block:: yaml

    key1: value1
    key2:
        key2.1: value2.1
        key2.2: value2.2
    key3: None

By comparison, the *in* step decorator, and the steps *contextset*,
*contextsetf* and *contextmerge* overwrite values that are in context already.

The recursive if-not-exists-then-set check happens for dictionaries, but not
for items in Lists, Sets and Tuples. You can set default values of type List,
Set or Tuple if their keys don't exist in context already, but this step will
not recurse through the List, Set or Tuple itself.

Supports `Substitutions`_. String interpolation applies to keys and values.

See a worked example for `default here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/default.yaml>`__.

pypyr.steps.echo
^^^^^^^^^^^^^^^^
Echo the context value ``echoMe`` to the output.

For example, if you had pipelines/mypipeline.yaml like this:

.. code-block:: yaml

  context_parser: pypyr.parser.keyvaluepairs
  steps:
    - name: pypyr.steps.echo

You can run:

.. code-block:: bash

  pypyr mypipeline "echoMe=Ceci n'est pas une pipe"


Alternatively, if you had pipelines/look-ma-no-params.yaml like this:

.. code-block:: yaml

  steps:
    - name: pypyr.steps.echo
      description: Output echoMe
      in:
        echoMe: Ceci n'est pas une pipe


You can run:

.. code-block:: bash

  $ pypyr look-ma-no-params

Supports `Substitutions`_.

pypyr.steps.env
^^^^^^^^^^^^^^^
Get, set or unset environment variables.

The ``env`` context key must exist. ``env`` can contain a combination of get,
set and unset keys.
You must specify at least one of ``get``, ``set`` and ``unset``.

.. code-block:: yaml

  env:
    get:
      contextkey1: env1
      contextkey2: env2
    set:
      env1: value1
      env2: value2
    unset:
      - env1
      - env2

This step will run whatever combination of Get, Set and Unset you specify.
Regardless of combination, execution order is Get, Set, Unset.

See a worked example `for environment variables here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/env_variables.yaml>`__.


env get
"""""""
Get $ENVs into the pypyr context.

If the $ENV does not exist, this step will raise an error. If you want to get
an $ENV that might not exist without throwing an error, use
`pypyr.steps.envget`_ instead.

``context['env']['get']`` must exist. It's a dictionary.

Values are the names of the $ENVs to write to the pypyr context.

Keys are the pypyr context item to which to write the $ENV values.

For example, say input context is:

.. code-block:: yaml

  key1: value1
  key2: value2
  pypyrCurrentDir: value3
  env:
    get:
      pypyrUser: USER
      pypyrCurrentDir: PWD


This will result in context:

.. code-block:: yaml

  key1: value1
  key2: value2
  key3: value3
  pypyrCurrentDir: <<value of $PWD here, not value3>>
  pypyrUser: <<value of $USER here>>

env set
"""""""
Set $ENVs from the pypyr context.

``context['env']['set']`` must exist. It's a dictionary.

Values are strings to write to $ENV. You can use {key} `Substitutions`_ to
format the string from context.
Keys are the names of the $ENV values to which to write.

For example, say input context is:

.. code-block:: yaml

  key1: value1
  key2: value2
  key3: value3
  env:
    set:
      MYVAR1: {key1}
      MYVAR2: before_{key3}_after
      MYVAR3: arbtexthere

This will result in the following $ENVs:

.. code-block:: yaml

  $MYVAR1 == value1
  $MYVAR2 == before_value3_after
  $MYVAR3 == arbtexthere

Note that the $ENVs are not persisted system-wide, they only exist for the
pypyr sub-processes, and as such for the subsequent steps during this pypyr
pipeline execution. If you set an $ENV here, don't expect to see it in your
system environment variables after the pipeline finishes running.

env unset
"""""""""
Unset $ENVs.

Context is a dictionary or dictionary-like. context is mandatory.

``context['env']['unset']`` must exist. It's a list.
List items are the names of the $ENV values to unset.

For example, say input context is:

.. code-block:: yaml

    key1: value1
    key2: value2
    key3: value3
    env:
      unset:
        - MYVAR1
        - MYVAR2

This will result in the following $ENVs being unset:

.. code-block:: bash

  $MYVAR1
  $MYVAR2

pypyr.steps.envget
^^^^^^^^^^^^^^^^^^
Get environment variables, and assign a default value to context if they do
not exist.

The difference between *pypyr.steps.envget* and *pypyr.steps.env* `env get`_,
is that *pypyr.steps.envget* won't raise an error if the $ENV doesn't exist.

The ``envget`` context key must exist.

.. code-block:: yaml

  - name: pypyr.steps.envget
    description: if env MACAVITY is not there, set context theHiddenPaw to default.
    in:
      envGet:
        env: MACAVITY
        key: theHiddenPaw
        default: but macavity wasn't there!


If you need to get more than one $ENV, you can pass a list to ``envget``.

.. code-block:: yaml

  envGet:
    # get >1 $ENVs by passing them in as list items
    - env: ENV_NAME1 # mandatory
      key: saveMeHere1 # mandatory
      default: null # optional
    - env: ENV_NAME2
      key: saveMeHere2
      default: 'use-me-if-env-not-there' # optional


- ``env``: Mandatory. This is the environment variable name. This is the bare
  environment variable name, do not put the $ in front of it.
- ``key``: Mandatory. The pypyr context key destination to which to copy the
  $ENV value.
- ``default`` Optional. Assign this value to ``key`` if the $ENV specified
  by ``env`` doesn't exist.

  - If you want to create a key in the pypyr context with an empty value,
    specify ``null``.
  - If you do NOT want to create a key in the pypyr context, do not have a
    default input.

.. code-block:: yaml

  # save ENV_NAME to key. If ENV_NAME doesn't exist, do NOT set saveMeHere.
  envGet:
    - env: ENV_NAME
      key: saveMeHere # saveMeHere won't be in context if ENV_NAME not there.
      # this is because the default keyword is not specified.

All inputs support `Substitutions`_.

See a worked example for `getting environment variables with defaults here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/envget.yaml>`__.


pypyr.steps.fetchjson
^^^^^^^^^^^^^^^^^^^^^
Loads a json file into the pypyr context.

This step requires the following key in the pypyr context to succeed:

.. code-block:: yaml

  fetchJson:
    path: ./path.json # required. path to file on disk. can be relative.
    key: 'destinationKey' # optional. write json to this context key.

If ``key`` is not specified, json writes directly to context root.

If you do not want to specify a key, you can also use the streamlined format:

.. code-block:: yaml

  fetchJson: ./path.json # required. path to file on disk. can be relative.

All inputs support `Substitutions`_.

Json parsed from the file will be merged into the pypyr context. This will
overwrite existing values if the same keys are already in there.

I.e if file json has ``{'eggs' : 'boiled'}``, but context ``{'eggs': 'fried'}``
already exists, returned ``context['eggs']`` will be 'boiled'.

If ``key`` is not specified, the json should not be an array [] at the
root level, but rather an Object {}.

See some worked examples of `fetchjson here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/fetchjson.yaml>`__.

pypyr.steps.fetchyaml
^^^^^^^^^^^^^^^^^^^^^
Loads a yaml file into the pypyr context.

This step requires the following key in the pypyr context to succeed:

.. code-block:: yaml

  fetchYaml:
    path: ./path.yaml # required. path to file on disk. can be relative.
    key: 'destinationKey' # optional. write yaml to this context key.

If ``key`` not specified, yaml writes directly to context root.

If you do not want to specify a key, you can also use the streamlined format:

.. code-block:: yaml

  fetchYaml: ./path.yaml # required. path to file on disk. can be relative.

All inputs support `Substitutions`_.

Yaml parsed from the file will be merged into the pypyr context. This will
overwrite existing values if the same keys are already in there.

I.e if file yaml has

.. code-block:: yaml

  eggs: boiled

but context ``{'eggs': 'fried'}`` already exists, returned ``context['eggs']``
will be 'boiled'.

If ``key`` is not specified, the yaml should not be a list at the top
level, but rather a mapping.

So the top-level yaml should not look like this:

.. code-block:: yaml

  - eggs
  - ham

but rather like this:

.. code-block:: yaml

  breakfastOfChampions:
    - eggs
    - ham

See some worked examples of `fetchyaml here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/fetchyaml.yaml>`__.

pypyr.steps.fileformat
^^^^^^^^^^^^^^^^^^^^^^
Parses input text file and substitutes {tokens} in the text of the file
from the pypyr context.

The following context keys expected:

- fileFormat

  - in

    - Mandatory path(s) to source file on disk.
    - This can be a string path to a single file, or a glob, or a list of paths
      and globs. Each path can be a relative or absolute path.

  - out

    - Write output file to here. Will create directories in path if these do not
      exist already.
    - *out* is optional. If not specified, will edit the *in* files in-place.
    - If in-path refers to >1 file (e.g it's a glob or list), out path can only
      be a directory - it doesn't make sense to write >1 file to the same
      single file output (this is not an appender.)
    - To ensure out_path is read as a directory and not a file, be sure to have
      the os' path separator (/ on a sane filesystem) at the end.
    - Files are created in the *out* directory with the same name they had in
      *in*.

So if you had a text file like this:

.. code-block:: text

  {k1} sit thee down and write
  In a book that all may {k2}

And your pypyr context were:

.. code-block:: yaml

  k1: pypyr
  k2: read

You would end up with an output file like this:

.. code-block:: text

  pypyr sit thee down and write
  In a book that all may read

Example with globs and a list. You can also pass a single string glob, it
doesn't need to be in a list.

.. code-block:: yaml

  fileFormat:
    in:
      # ** recurses sub-dirs per usual globbing
      - ./testfiles/sub3/**/*.txt
      - ./testfiles/??b/fileformat-in.*.txt
    # note the dir separator at the end.
    # since >1 in files, out can only be a dir.
    out: ./out/replace/

If you do not specify *out*, it will over-write (i.e edit) all the files
specified by *in*.

.. code-block:: yaml

  fileFormat:
    # in-place edit/overwrite all the files in. this can also be a glob, or
    # a mixed list of paths and/or globs.
    in: ./infile.txt

The file in and out paths support `Substitutions`_.

See a worked example of
`fileformat here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/fileformat.yaml>`_.

pypyr.steps.fileformatjson
^^^^^^^^^^^^^^^^^^^^^^^^^^
Parses input json file and substitutes {tokens} from the pypyr context.

Pretty much does the same thing as `pypyr.steps.fileformat`_, only it makes it
easier to work with curly braces for substitutions without tripping over the
json's structural braces.

The following context keys expected:

- fileFormatJson

  - in

    - Mandatory path(s) to source file on disk.
    - This can be a string path to a single file, or a glob, or a list of paths
      and globs. Each path can be a relative or absolute path.

  - out

    - Write output file to here. Will create directories in path if these do not
      exist already.
    - *out* is optional. If not specified, will edit the *in* files in-place.
    - If in-path refers to >1 file (e.g it's a glob or list), out path can only
      be a directory - it doesn't make sense to write >1 file to the same
      single file output (this is not an appender.)
    - To ensure out_path is read as a directory and not a file, be sure to have
      the os' path separator (/ on a sane filesystem) at the end.
    - Files are created in the *out* directory with the same name they had in
      *in*.

See `pypyr.steps.fileformat`_ for more examples on in/out path handling - the
same processing rules apply.

Example with a glob input:

.. code-block:: yaml

  fileFormatJson:
    in: ./testfiles/sub3/**/*.txt
    # note the dir separator at the end.
    # since >1 in files, out can only be a dir.
    out: ./out/replace/

If you do not specify *out*, it will over-write (i.e edit) all the files
specified by *in*.

`Substitutions`_ enabled for keys and values in the source json.

The file in and out paths also support `Substitutions`_.

See a worked example of
`fileformatjson here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/fileformatjson.yaml>`_.

pypyr.steps.fileformatyaml
^^^^^^^^^^^^^^^^^^^^^^^^^^
Parses input yaml file and substitutes {tokens} from the pypyr context.

Pretty much does the same thing as `pypyr.steps.fileformat`_, only it makes it
easier to work with curly braces for substitutions without tripping over the
yaml's structural braces. If your yaml doesn't use curly braces that aren't
meant for {token} substitutions, you can happily use `pypyr.steps.fileformat`_
instead - it's more memory efficient.

This step does not preserve comments. Use `pypyr.steps.fileformat`_ if you need
to preserve comments on output.

The following context keys expected:

- fileFormatYaml

  - in

    - Mandatory path(s) to source file on disk.
    - This can be a string path to a single file, or a glob, or a list of paths
      and globs. Each path can be a relative or absolute path.

  - out

    - Write output file to here. Will create directories in path if these do not
      exist already.
    - *out* is optional. If not specified, will edit the *in* files in-place.
    - If in-path refers to >1 file (e.g it's a glob or list), out path can only
      be a directory - it doesn't make sense to write >1 file to the same
      single file output (this is not an appender.)
    - To ensure out_path is read as a directory and not a file, be sure to have
      the os' path separator (/ on a sane filesystem) at the end.
    - Files are created in the *out* directory with the same name they had in
      *in*.

See `pypyr.steps.fileformat`_ for more examples on in/out path handling - the
same processing rules apply.

Example with a glob input and a normal path in a list:

.. code-block:: yaml

  fileFormatYaml:
    in: [./file1.yaml, ./testfiles/sub3/**/*.yaml]
    # note the dir separator at the end.
    # since >1 in files, out can only be a dir.
    out: ./out/replace/

If you do not specify *out*, it will over-write (i.e edit) all the files
specified by *in*.

The file in and out paths support `Substitutions`_.

See a worked example of
`fileformatyaml
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/fileformatyaml.yaml>`_.

pypyr.steps.filereplace
^^^^^^^^^^^^^^^^^^^^^^^
Parses input text file and replaces a search string.

The other *fileformat* steps, by way of contradistinction, uses string
formatting expressions inside {braces} to format values against the pypyr
context. This step, however, let's you specify any search string and replace it
with any replace string. This is handy if you are in a file where curly braces
aren't helpful for a formatting expression - e.g inside a .js file.

The following context keys expected:

- fileReplace

  - in

    - Mandatory path(s) to source file on disk.
    - This can be a string path to a single file, or a glob, or a list of paths
      and globs. Each path can be a relative or absolute path.

  - out

    - Write output file to here. Will create directories in path if these do not
      exist already.
    - *out* is optional. If not specified, will edit the *in* files in-place.
    - If in-path refers to >1 file (e.g it's a glob or list), out path can only
      be a directory - it doesn't make sense to write >1 file to the same
      single file output (this is not an appender.)
    - To ensure out_path is read as a directory and not a file, be sure to have
      the os' path separator (/ on a sane filesystem) at the end.
    - Files are created in the *out* directory with the same name they had in
      *in*.

  - replacePairs

    - dictionary where format is:

      - 'find_string': 'replace_string'

Example input context:

.. code-block:: yaml

  fileReplace:
    in: ./infile.txt
    out: ./outfile.txt
    replacePairs:
      findmestring: replacewithme
      findanotherstring: replacewithanotherstring
      alaststring: alastreplacement


Example with globs and a list. You can also pass a single string glob.

.. code-block:: yaml

  fileReplace:
    in:
      # ** recurses sub-dirs per usual globbing
      - ./testfiles/replace/sub/**
      - ./testfiles/replace/*.ext
    # note the dir separator at the end.
    # since >1 in files, out can only be a dir.
    out: ./out/replace/
    replacePairs:
        findmestring: replacewithme

If you do not specify *out*, it will over-write (i.e edit) all the files
specified by *in*.

.. code-block:: yaml

  fileReplace:
    # in-place edit/overwrite all the files in
    in: ./infile.txt
    replacePairs:
      findmestring: replacewithme

fileReplace also does string substitutions from context on the replacePairs. It
does this before it search & replaces the *in* file.

Be careful of order. The last string replacement expression could well replace
a replacement that an earlier replacement made in the sequence.

If replacePairs is not an ordered collection, replacements could evaluate in
any given order. If you are creating your *in* parameters in the pipeline yaml,
don't worry about it, it will be an ordered dictionary already, so life is good.

The file in and out paths support `Substitutions`_.

See a worked
`example here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/filereplace.yaml>`_.

pypyr.steps.filewritejson
^^^^^^^^^^^^^^^^^^^^^^^^^
Write a payload to a json file on disk.

*filewritejson* expects the following input context:

.. code-block:: yaml

  fileWriteJson:
    path: /path/to/output.json # destination file
    payload: # payload to write to path
      key1: value1 # output json will have
      key2: value2 # key1 and key2.

If you do not specify *payload*, pypyr will write the entire context to the
output file in json format. Be careful if you have sensitive values like
passwords or private keys!

All inputs support `Substitutions`_. This means you can specify another context
item to be the path and/or the payload, for example:

.. code-block:: yaml

  arbkey: arbvalue
  writehere: /path/to/output.json
  writeme:
    this: json content
    will: be written to
    thepath: with substitutions like this {arbkey}.
  fileWriteJson:
    path: '{writehere}'
    payload: '{writeme}'

Substitution processing runs on the output. In the above example, in the output
json file created at */path/to/output.json*, the ``{arbkey}`` expression in
the last line will substitute like this:

.. code-block:: json

  {
      "this": "json content",
      "will": "be written to",
      "thepath": "with substitutions like this arbvalue."
  }

See a worked `filewritejson example here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/filewritejson.yaml>`_.

pypyr.steps.filewriteyaml
^^^^^^^^^^^^^^^^^^^^^^^^^
Write a payload to a yaml file on disk.

*filewriteyaml* expects the following input context:

.. code-block:: yaml

  fileWriteYaml:
    path: /path/to/output.yaml # destination file
    payload: # payload to write to path
      key1: value1 # output yaml will have
      key2: value2 # key1 and key2.

If you do not specify *payload*, pypyr will write the entire context to the
output file in yaml format. Be careful if you have sensitive values like
passwords or private keys!

All inputs support `Substitutions`_. This means you can specify another context
item to be the path and/or the payload, for example:

.. code-block:: yaml

  arbkey: arbvalue
  writehere: /path/to/output.yaml
  writeme:
    this: yaml content
    will: be written to
    thepath: with substitutions like this {arbkey}.
  fileWriteYaml:
    path: '{writehere}'
    payload: '{writeme}'

Substitution processing runs on the output. In the above example, in the output
yaml file created at */path/to/output.yaml*, the ``{arbkey}`` expression in
the last line will substitute like this:

.. code-block:: yaml

  this: yaml content
  will: be written to
  thepath: with substitutions like this arbvalue.

See a worked `filewriteyaml example here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/filewriteyaml.yaml>`_.

pypyr.steps.glob
^^^^^^^^^^^^^^^^
Resolves a glob and gets all the paths that exist on the filesystem for the
input glob.

A path can point to a file or a directory.

The ``glob`` context key must exist.

.. code-block:: yaml

  - name: pypyr.steps.glob
    in:
      glob: ./**/*.py # single glob

If you want to resolve multiple globs simultaneously and combine the results,
you can pass a list instead. You can freely mix literal paths and globs.

.. code-block:: yaml

  - name: pypyr.steps.glob
    in:
      glob:
        - ./file1 # literal relative path
        - ./dirname # also finds dirs
        - ./**/{arbkey}* # glob with a string formatting expression

After *glob* completes, the ``globOut`` context key is available.
This contains the results of the *glob* operation.

.. code-block:: yaml

  globOut: # list of strings. Paths of all files found.
      ['file1', 'dir1', 'blah/arb']

You can use ``globOut`` as the list to enumerate in a ``foreach`` decorator
step, to run a step for each file found.

.. code-block:: yaml

  - name: pypyr.steps.glob
    in:
     glob: ./get-files/**/*
  - name: pypyr.steps.pype
    foreach: '{globOut}'
    in:
      pype:
        name: pipeline-does-something-with-single-file

All inputs support `Substitutions`_. This means you can specify another context
item to be an individual path, or part of a path, or the entire path list.

See a worked
example for `glob here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/glob.yaml>`_.

pypyr.steps.jump
^^^^^^^^^^^^^^^^
Jump to another step-group. This effectively stops processing on the current
step-group you are jumping from.

If you want to return to the point of origin after the step-group you
jumped to completes, use `pypyr.steps.call`_ instead.

*jump* expects a context item *jump*. It can take one of two forms:

.. code-block:: yaml

  - name: pypyr.steps.jump
    comment: simple string means just call the step-group named "jumphere"
    in:
      jump: jumphere
  - name: pypyr.steps.call
    comment: specify groups, success and failure.
    in:
      jump:
        groups: ['jumphere', 'andhere'] # list. Step-group sequence to jump to.
        success: group_to_call_on_success # string. Single step-group name.
        failure: group_to_call_on_failure # string. Single step-group name.

*jump.groups* can be a simple string if you're just jumping a single group -
i.e you don't need to make it a list of one item.

Jump is handy when you want to transfer control from a current step-group to
a different sequence of steps. So you can jump around to your heart's content.

.. code-block:: yaml

  steps:
    - name: pypyr.steps.echo
      in:
        echoMe: this is the 1st step of steps
    - name: pypyr.steps.jump
      in:
        jump: arbgroup
    - name: pypyr.steps.echo
      in:
       echoMe: You WON'T see me because we jumped.
  arbgroup:
      - name: pypyr.steps.echo
        in:
          echoMe: this is arb group
      - pypyr.steps.stopstepgroup
      - name: pypyr.steps.echo
        in:
          echoMe: if you see me something is WRONG.


This will result in:

.. code-block:: text

  NOTIFY:pypyr.steps.echo:run_step: this is the 1st step of steps
  NOTIFY:pypyr.steps.echo:run_step: this is arb group


Jump only runs success or failure groups if you actually specify these.

All inputs support string `Substitutions`_.

See a worked example for `jump here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/jump.yaml>`__.

pypyr.steps.pathcheck
^^^^^^^^^^^^^^^^^^^^^
Check if a path exists on the filesystem. Supports globbing. A path can point
to a file or a directory.

The ``pathCheck`` context key must exist.

.. code-block:: yaml

  - name: pypyr.steps.pathcheck
    in:
      pathCheck: ./**/*.py # single path with glob

If you want to check for the existence of multiple paths, you can pass a list
instead. You can freely mix literal paths and globs.

.. code-block:: yaml

  - name: pypyr.steps.pathcheck
    in:
      pathCheck:
        - ./file1 # literal relative path
        - ./dirname # also finds dirs
        - ./**/{arbkey}* # glob with a string formatting expression

After *pathcheck* completes, the ``pathCheckOut`` context key is available.
This contains the results of the *pathcheck* operation.

.. code-block:: yaml

  pathCheckOut:
      # the key is the ORIGINAL input, no string formatting applied.
      'inpath-is-the-key': # one of these for each pathCheck input
          exists: true # bool. True if path exists.
          count: 0 # int. Number of files found for in path.
          found: ['path1', 'path2'] # list of strings. Paths of files found.

Example of passing a single input and the expected output context:

.. code-block:: yaml

  pathCheck: ./myfile # assuming ./myfile exists in $PWD
  pathCheckOut:
    './myfile':
      exists: true,
      count: 1,
      found:
        - './myfile'

The ``exists`` and ``count`` keys can be very useful for conditional
decorators to help decide whether to run subsequent steps. You can use these
directly in string formatting expressions without any extra fuss.

.. code-block:: yaml

  - name: pypyr.steps.pathcheck
    in:
      pathCheck: ./**/*.arb
  - name: pypyr.steps.echo
    run: '{pathCheckOut[./**/*.arb][exists]}'
    in:
      echoMe: you'll only see me if ./**/*.arb found something on filesystem.

All inputs support `Substitutions`_. This means you can specify another context
item to be an individual path, or part of a path, or the entire path list.

See a worked
example for `pathcheck here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/pathcheck.yaml>`_.

pypyr.steps.py
^^^^^^^^^^^^^^
Executes the context value `pycode` as python code.

Will exec ``context['pycode']`` as a dynamically interpreted python code block.

You can access and change the context dictionary in a py step. See a worked
example `here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/py.yaml>`_.

For example, this will invoke python print and print 2:

.. code-block:: yaml

  steps:
    - name: pypyr.steps.py
      description: Example of an arb python command. Will print 2.
      in:
        pycode: print(1+1)

pypyr.steps.pype
^^^^^^^^^^^^^^^^
Overview
""""""""
Run another pipeline from this step. This allows pipelines to invoke other
pipelines. Why pype? Because the pypyr can pipe that song again.

*pype* is handy if you want to split a larger, cumbersome pipeline into smaller
units. This helps testing, in that you can test smaller units as
separate pipelines without having to re-run the whole pipeline each time. This
gets pretty useful for longer running sequences where the first steps are not
idempotent but you do want to iterate over the last steps in the pipeline.
Provisioning or deployment scripts frequently have this sort of pattern: where
the first steps provision expensive resources in the environment and later steps
just tweak settings on the existing environment.

The parent pipeline is the current, executing pipeline. The invoked, or child,
pipeline is the pipeline you are calling from this step.

See here for worked example of `pype
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/pype.yaml>`_.

Context properties
""""""""""""""""""
Example input context:

.. code-block:: yaml

  pype:
    name: 'pipeline name' # mandatory. string.
    args: # optional. Defaults None.
      inputkey: value
      anotherkey: anothervalue
    out: # optional. Defaults None.
      parentkey: childkey
      parentkey2: childkey2
    groups: [group1, group2] # optional. Defaults "steps".
    success: 'success group' # optional. Defaults "on_success".
    failure: 'failure group' # optional. Defaults "on_failure".
    pipeArg: 'argument here' # optional. string.
    raiseError: True # optional. bool. Defaults True.
    skipParse: True # optional. bool. Defaults True.
    useParentContext: True  # optional. bool. Defaults True.
    loader: None # optional. string. Defaults to standard file loader.


All inputs supports string `Substitutions`_.

+-----------------------+------------------------------------------------------+
| **pype property**     | **description**                                      |
+-----------------------+------------------------------------------------------+
| name                  | Name of child pipeline to execute. This {name}.yaml  |
|                       | must exist in the *working directory* dir.           |
+-----------------------+------------------------------------------------------+
| args                  | Run child pipeline with these args. These args       |
|                       | create a fresh context for the child pipeline that   |
|                       | contains only the key/values that you set here.      |
|                       |                                                      |
|                       | If you set *args*, you implicitly set                |
|                       | *useParentContext* to False. If you explicitly set   |
|                       | *useParentContext* to True AND you specify *args*,   |
|                       | the args will be merged into the parent context      |
|                       | and {formatting expressions} applied before running  |
|                       | the child pipeline.                                  |
+-----------------------+------------------------------------------------------+
| out                   | If the child pipeline ran with a fresh new Context,  |
|                       | because you set *args* or you set *useParentContext* |
|                       | to False, *out* saves values from the child pipeline |
|                       | context back to the parent context.                  |
|                       |                                                      |
|                       | *out* can take 3 forms:                              |
|                       |                                                      |
|                       | .. code-block:: yaml                                 |
|                       |                                                      |
|                       |   # save key1 from child to parent                   |
|                       |   out: 'key1'                                        |
|                       |   # or save list of keys from child to parent        |
|                       |   out: ['key1', 'key2']                              |
|                       |   # or map child keys to different parent keys       |
|                       |   out:                                               |
|                       |     'parent-destination-key1': 'child-key1'          |
|                       |     'parent-destination-key2': 'child-key2'          |
+-----------------------+------------------------------------------------------+
| groups                | Run only these step-groups in the child pipeline.    |
|                       | Equivalent to *groups* arg on the pypyr cli.         |
|                       |                                                      |
|                       | If you don't set this, pypyr will just run the       |
|                       | *steps* step-group as per usual.                     |
|                       |                                                      |
|                       | If you only want to run a single group, you can set  |
|                       | it simply as a string, not a list, like this:        |
|                       |                                                      |
|                       | ``groups: mygroupname``                              |
|                       |                                                      |
|                       | If you set groups, success and failure do not default|
|                       | to *on_success* and *on_failure* anymore. In other   |
|                       | words, pype will only run the groups you specifically|
|                       | specified. If you still want success/failure handlers|
|                       | explicitly set these with *success* & *failure*.     |
+-----------------------+------------------------------------------------------+
| success               | Run this step-group on successful completion of the  |
|                       | child pipeline's step *groups*.                      |
|                       |                                                      |
|                       | Equivalent to *success* arg on the pypyr cli.        |
|                       |                                                      |
|                       | If you don't set this, pypyr will just run the       |
|                       | *on_success* step-group as per usual if it exists.   |
|                       |                                                      |
|                       | If you specify *success*, but you don't set *groups*,|
|                       | pypyr will default to running the standard *steps*   |
|                       | group as entry-point for the child pipeline.         |
+-----------------------+------------------------------------------------------+
| failure               | Run this step-group on an error occurring in the     |
|                       | child pipeline's step *groups*.                      |
|                       |                                                      |
|                       | Equivalent to *failure* arg on the pypyr cli.        |
|                       |                                                      |
|                       | If you don't set this, pypyr will just run the       |
|                       | *on_failure* step-group as per usual if it exists.   |
|                       |                                                      |
|                       | If you specify *failure*, but you don't set *groups*,|
|                       | pypyr will default to running the standard *steps*   |
|                       | group as entry-point for the child pipeline.         |
+-----------------------+------------------------------------------------------+
| pipeArg               | String to pass to the child pipeline context_parser. |
|                       | Equivalent to *context* arg on the pypyr cli. Only   |
|                       | used if skipParse==False                             |
+-----------------------+------------------------------------------------------+
| raiseError            | If True, errors in child raised up to parent.        |
|                       |                                                      |
|                       | If False, log and swallow any errors that happen     |
|                       | during the invoked pipeline's execution. Swallowing  |
|                       | means that the current/parent pipeline will carry on |
|                       | with the next step even if an error occurs in the    |
|                       | invoked pipeline.                                    |
+-----------------------+------------------------------------------------------+
| skipParse             | If True, skip the context_parser on the invoked      |
|                       | pipeline.                                            |
|                       |                                                      |
|                       | This is relevant if your child-pipeline uses a       |
|                       | context_parser to initialize context when you test   |
|                       | it in isolation by running it directly from the cli, |
|                       | but when calling from a parent pipeline the parent   |
|                       | is responsible for creating the appropriate context. |
+-----------------------+------------------------------------------------------+
| useParentContext      | If True, passes the parent's context to the child.   |
|                       | Any changes to the context by the child will be      |
|                       | available to the parent when the child completes.    |
|                       |                                                      |
|                       | If False, the child creates its own, fresh context   |
|                       | that does not contain any of the parent's keys. The  |
|                       | child's context is destroyed upon completion of the  |
|                       | child pipeline and updates to the child context do   |
|                       | not reach the parent context.                        |
+-----------------------+------------------------------------------------------+
| loader                | Load the child pipeline with this loader. The        |
|                       | default is the standard pypyr                        |
|                       | pypyr.pypeloaders.fileloader, which looks for pypes  |
|                       | in the ./pipelines directory.                        |
+-----------------------+------------------------------------------------------+

Roll your own pype loaders
""""""""""""""""""""""""""
A pype loader is responsible for loading a pipeline. By default pypyr gets
pypes from the local ./pipelines/pypename.yaml location.

The default pype loader is *pypyr.pypeloaders.fileloader*.

If you want to load pypes from somewhere else, like maybe a shared pype library,
or implement caching, or maybe from something like s3, you can roll your own
pype loader.

.. code-block:: python

  import logging
  from pypyr.errors import PipelineNotFoundError
  import pypyr.yaml

  # use pypyr logger to ensure loglevel is set correctly
  logger = logging.getLogger(__name__)

  def get_pipeline_definition(pipeline_name, working_dir):
      """Open and parse the pipeline definition yaml.

      Parses pipeline yaml and returns dictionary representing the pipeline.

      pipeline_name is whatever is passed in from the shell like:
      pypyr pipelinename args

      Args:
          pipeline_name: string. Name of pipeline. This will be the file-name of
                         the pipeline - i.e {pipeline_name}.yaml
                         Passed in from the shell 1st positional argument.
          working_dir: path. passed in from the shell --dir switch.

      Returns:
          dict describing the pipeline, parsed from the pipeline yaml.

      Raises:
          PipelineNotFoundError: pipeline_name not found.

      """
      logger.debug("starting")

      # it's good form only to use .info and higher log levels when you must.
      # For .debug() being verbose is very much encouraged.
      logger.info("Your clever code goes here. . . ")

      yaml_file = your_clever_function_that_gets_a_filelike_object_from_somewhere()
      pipeline_definition = pypyr.yaml.get_pipeline_yaml(yaml_file)

      logger.debug(
          f"found {len(pipeline_definition)} stages in pipeline.")

      logger.debug("pipeline definition loaded")

      logger.debug("done")
      return pipeline_definition

Recursion
"""""""""
Yes, you can pype recursively - i.e a child pipeline can call its antecedents.
It's up to you to avoid infinite recursion, though. Since we're all responsible
adults here, pypyr does not protect you from infinite recursion other than the
default python recursion limit. So don't come crying if you blew your stack. Or
a seal.

Here is a worked example of `pype recursion
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/pype-recursion.yaml>`_.

pypyr.steps.pypyrversion
^^^^^^^^^^^^^^^^^^^^^^^^
Outputs the same as:

.. code-block:: bash

  pypyr --version

This is an actual pipeline, though, so unlike --version, it'll use the standard
pypyr logging format.

Example pipeline yaml:

.. code-block:: yaml

    steps:
      - pypyr.steps.pypyrversion

pypyr.steps.now
^^^^^^^^^^^^^^^
Writes the current local date & time to context *now*. Also known as wall time.

If you want UTC time, check out `pypyr.steps.nowutc`_ instead.

If you run this step as a simple step (with no input *nowIn* formatting), the
default datetime format is ISO8601. For example:
*YYYY-MM-DDTHH:MM:SS.ffffff+00:00*

You can use explicit format strings to control the datetime representation. For
a full list of available formatting codes, check here:
https://docs.python.org/3.7/library/datetime.html#strftime-and-strptime-behavior

.. code-block:: yaml

  - pypyr.steps.now # this sets {now} to YYYY-MM-DDTHH:MM:SS.ffffff+00:00
  - name: pypyr.steps.echo
    in:
      echoMe: 'timestamp in ISO8601 format: {now}'
  - name: pypyr.steps.now
    description: use a custom date format string instead of the default ISO8601
    in:
      nowIn: '%A %Y %m/%d %H:%M in timezone %Z offset %z, localized to %x'
  - name: pypyr.steps.echo
    in:
      echoMe: 'the custom formatting for now was set in the previous step. {now}'
  - pypyr.steps.now # subsequent simple step calls will re-use previously set
                    # nowIn for formatting, but refresh the timestamp.


Supports string `Substitutions`_.

See a worked example for `now here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/now.yaml>`__.

pypyr.steps.nowutc
^^^^^^^^^^^^^^^^^^
Writes the current UTC date & time to context *nowUtc*.

If you want local or wall time, check out `pypyr.steps.now`_ instead.

If you run this step as a simple step (with no input *nowUtcIn* formatting), the
default datetime format is ISO8601. For example:
*YYYY-MM-DDTHH:MM:SS.ffffff+00:00*

You can use explicit format strings to control the datetime representation. For
a full list of available formatting codes, check here:
https://docs.python.org/3.7/library/datetime.html#strftime-and-strptime-behavior

.. code-block:: yaml

  - pypyr.steps.nowutc # this sets {nowUtc} to YYYY-MM-DDTHH:MM:SS.ffffff+00:00
  - name: pypyr.steps.echo
    in:
      echoMe: 'utc timestamp in ISO8601 format: {nowUtc}'
  - name: pypyr.steps.nowutc
    description: use a custom date format string instead of the default ISO8601
    in:
      nowUtcIn: '%A %Y %m/%d %H:%M in timezone %Z offset %z, localized to %x'
  - name: pypyr.steps.echo
    in:
      echoMe: 'the custom formatting was set in the previous step: {nowUtc}'
  - pypyr.steps.nowutc # subsequent simple step calls will re-use previously set
                       # nowUtcIn for formatting, but refresh the timestamp.


Supports string `Substitutions`_.

See a worked example for `nowutc here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/now.yaml>`__.

pypyr.steps.safeshell
^^^^^^^^^^^^^^^^^^^^^
Alias for `pypyr.steps.cmd`_.

Example pipeline yaml:

.. code-block:: yaml

  steps:
    - name: pypyr.steps.safeshell
      in:
        cmd: ls -a

pypyr.steps.shell
^^^^^^^^^^^^^^^^^
Runs the context value `cmd` in the default shell. On a sensible O/S, this is
`/bin/sh`

Do all the things you can't do with `pypyr.steps.cmd`_.

Input context can take one of two forms:

.. code-block:: yaml

  - name: pypyr.steps.shell
    description: passing cmd as a string does not save the output to context.
                 it prints stdout in real-time.
    in:
      cmd: 'echo ${PWD}'
  - name: pypyr.steps.shell
    description: passing cmd as a dict allows you to specify if you want to
                 save the output to context.
                 it prints command output only AFTER it has finished running.
    in:
      cmd:
        run: 'echo ${PWD}'
        save: True
        cwd: './current/working/dir/here'

If ``cwd`` is specified, will change the current working directory to *cwd* to
execute this command. The directory change is only for the duration of this
step, not any subsequent steps. If *cwd* is specified, the executable or program
specified in *run* is relative to the *cwd* if the *run* cmd uses relative paths.

If ``cwd`` is not specified, defaults to the current working directory, which
is from wherever you are running ``pypyr``.

Be aware that if *save* is True, all of the command output ends up in memory.
Don't specify it unless your pipeline uses the stdout/stderr response in
subsequent steps. Keep in mind that if the invoked command return code returns
a non-zero return code pypyr will automatically raise a *CalledProcessError*
and stop the pipeline.

If save is True, pypyr will save the output to context as follows:

.. code-block:: yaml

    cmdOut:
        returncode: 0
        stdout: 'stdout str here. None if empty.'
        stderr: 'stderr str here. None if empty.'

*cmdOut.returncode* is the exit status of the called process. Typically 0 means
OK. A negative value -N indicates that the child was terminated by signal N
(POSIX only).

You can use cmdOut in subsequent steps like this:

.. code-block:: yaml

  - name: pypyr.steps.echo
    run: !py "cmdOut['returncode'] == 0"
    in:
      echoMe: "you'll only see me if cmd ran successfully with return code 0.
              the command output was: {cmdOut[stdout]}"

Friendly reminder of the difference between separating your commands with ; or
&&:

- ; will continue to the next statement even if the previous command errored.
  It won't exit with an error code if it wasn't the last statement.
- && stops and exits reporting error on first error.

You can change directory multiple times during this shell step using ``cd``,
but dir changes are only in scope for subsequent commands in this step, not for
subsequent steps. Instead prefer using the ``cwd`` input as described above for
an easy life, which sets the working directory for the entire step without you
having to code it in with chained shell commands.

.. code-block:: yaml

  - name: pypyr.steps.shell
    description: hop one up from current working dir. sic means won't attempt
                 to substitute {PWD} from context.
    in:
      cmd: !sic echo ${PWD}; cd ../; echo ${PWD}
  - name: pypyr.steps.shell
    description: back to your current working dir
    in:
      cmd: !sic echo ${PWD}

Supports string `Substitutions`_.

Example pipeline yaml using a pipe:

.. code-block:: bash

  steps:
    - name: pypyr.steps.shell
      in:
        cmd: ls | grep pipe; echo if you had something pipey it should show up;
    - name: pypyr.steps.shell
      description: if you want to pass curlies to the shell, use sic strings
      in:
        cmd: !sic echo ${PWD};

See a worked example `for shell power here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/shell.yaml>`__.

pypyr.steps.stop
^^^^^^^^^^^^^^^^
Stop all pypyr processing immediately. Doesn't run any success or failure
handlers, it just stops everything in its tracks, even when you're nested
in child pipelines or a step-group call-chain.

You can always use ``pypyr.steps.stop`` as a simple step.

.. code-block:: yaml

  - name: pypyr.steps.echo
    in:
      echoMe: you'll see me...
  - pypyr.steps.stop
  - name: pypyr.steps.echo
    in:
      echoMe: you WON'T see me...


See a worked example `for stop here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/stop.yaml>`__.


pypyr.steps.stoppipeline
^^^^^^^^^^^^^^^^^^^^^^^^
Stop current pipeline. Doesn't run any success or failure handlers, it just
stops the current pipeline.

This is handy if you are using ``pypyr.steps.pype`` to call child pipelines
from a parent pipeline, allowing you to stop just a child pipeline but letting
the parent pipeline continue.

You can always use ``pypyr.steps.stoppipeline`` as a simple step.

.. code-block:: yaml

  - name: pypyr.steps.echo
    in:
      echoMe: you'll see me...
  - pypyr.steps.stoppipeline
  - name: pypyr.steps.echo
    in:
      echoMe: you WON'T see me...


See a worked example `for stop pipeline here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/stop-pipeline.yaml>`__.

pypyr.steps.stopstepgroup
^^^^^^^^^^^^^^^^^^^^^^^^^
Stop current step-group. Doesn't run any success or failure handlers, it just
stops the current step-group.

This is handy if you are using ``pypyr.steps.call`` or ``pypyr.steps.jump``
to run different step-groups, allowing you to stop just a child step-group but
letting the parent step-group continue.

You can always use ``pypyr.steps.stopstepgroup`` as a simple step.

.. code-block:: yaml

  steps:
    - name: pypyr.steps.call
      in:
        call:
          groups: arbgroup
    - name: pypyr.steps.echo
      in:
       echoMe: You'll see me because only arbgroup was stopped.

  arbgroup:
      - name: pypyr.steps.echo
        in:
          echoMe: this is arb group
      - pypyr.steps.stopstepgroup
      - name: pypyr.steps.echo
        in:
          echoMe: if you see me something is WRONG.


See a worked example `for stop step-group here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/stop-stepgroup.yaml>`__.

pypyr.steps.tar
^^^^^^^^^^^^^^^
Archive and/or extract tars with or without compression.

.. code-block:: yaml

  tar:
      extract:
          - in: /path/my.tar
            out: /out/path
      archive:
          - in: /dir/to/archive
            out: /out/destination.tar
      format: ''

Either ``extract`` or ``archive`` should exist, or both. But not neither.

Optionally, you can also specify the tar compression format with
``format``. If not specified, defaults to *lzma/xz*
Available options for ``format``:

- ``''`` - no compression
- ``gz`` (gzip)
- ``bz2`` (bzip2)
- ``xz`` (lzma)

This step will run whatever combination of Extract and Archive you specify.
Regardless of combination, execution order is Extract, then Archive.

Never extract archives from untrusted sources without prior inspection. It is
possible that files are created outside of path, e.g. members that have
absolute filenames starting with "/" or filenames with two dots "..".

See a worked example `for tar here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/tar.yaml>`__.

tar extract
"""""""""""
``tar['extract']`` must exist. It's a list of dictionaries.

keys are the path to the tar to extract.

values are the destination paths.

You can use {key} substitutions to format the string from context. See
`Substitutions`_.

.. code-block:: yaml

  key1: here
  key2: tar.xz
  tar:
    extract:
      - in: path/to/my.tar.xz
        out: /path/extract/{key1}
      - in: another/{key2}
        out: .

This will:

- Extract *path/to/my.tar.xz* to */path/extract/here*
- Extract *another/tar.xz* to the current execution directory

  - This is the directory you're running pypyr from, not the pypyr pipeline
    working directory you set with the ``--dir`` flag.

tar archive
"""""""""""
``tar['archive']`` must exist. It's a list of dictionaries.

keys are the paths to archive.

values are the destination output paths.

You can use {key} substitutions to format the string from context. See
`Substitutions`_.

.. code-block:: yaml

  key1: destination.tar.xz
  key2: value2
  tar:
    archive:
      - in: path/{key2}/dir
        out: path/to/{key1}
      - in: another/my.file
        out: ./my.tar.xz

This will:

- Archive directory *path/value2/dir* to *path/to/destination.tar.xz*,
- Archive file *another/my.file* to *./my.tar.xz*


Roll your own step
------------------
.. code-block:: python

  import logging


  # getLogger will grab the parent logger context, so your loglevel and
  # formatting will inherit correctly automatically from the pypyr core.
  logger = logging.getLogger(__name__)


  def run_step(context):
      """Run code in here. This shows you how to code a custom pipeline step.

      :param context: dictionary-like type
      """
      logger.debug("started")
      # you probably want to do some asserts here to check that the input context
      # dictionary contains the keys and values you need for your code to work.
      assert 'mykeyvalue' in context, ("context['mykeyvalue'] must exist for my clever step.")

      # it's good form only to use .info and higher log levels when you must.
      # For .debug() being verbose is very much encouraged.
      logger.info("Your clever code goes here. . . ")

      # Add or edit context items. These are available to any pipeline steps
      # following this one.
      context['existingkey'] = 'new value overwrites old value'
      context['mynewcleverkey'] = 'new value'

      logger.debug("done")

on_success
==========
on_success is a list of steps to execute in sequence. Runs when `steps:`
completes successfully.

You can use built-in steps or code your own steps exactly like you would for
steps - it uses the same function signature.

on_failure
==========
on_failure is a list of steps to execute in sequence. Runs when any of the
above hits an unhandled exception.

If on_failure encounters another exception while processing an exception, then
both that exception and the original cause exception will be logged.

You can use built-in steps or code your own steps exactly like you would for
steps - it uses the same function signature.

******
Errors
******
*pypyr* runs pipelines. . . and a pipeline is a sequence of steps. Philosophically,
*pypyr* assumes that any error is a hard stop, unless you explicitly tell
*pypyr* differently.

*pypyr* saves all run-time errors to a list in context called *runErrors*.

.. code-block:: yaml

  runErrors:
    - name: Error Name Here
      description: Error Description Here
      customError: # whatever you put into onError on step definition
      line: 1 # line in pipeline yaml for failing step
      col: 1 # column in pipeline yaml for failing step
      step: my.bad.step.name # failing step name
      exception: ValueError('arb') # the actual python error object
      swallowed: False # True if err was swallowed

The last error will be the last item in the list. The first error will be the
first item in the list.

This is handy if you use the *swallow* step decorator to swallow an error or
bunch of errors, but you still want to do things in subsequent steps with the
error information.

*************
Substitutions
*************
string interpolation
====================
You can use substitution tokens, aka string interpolation, where specified for
context items. This substitutes anything between {curly braces} with the
context value for that key. This also works where you have dictionaries/lists
inside dictionaries/lists. For example, if your context looked like this:

.. code-block:: yaml

  key1: down
  key2: valleys
  key3: value3
  key4: "Piping {key1} the {key2} wild"

The value for ``key4`` will be "Piping down the valleys wild".

Escape literal curly braces with doubles: {{ for {, }} for }

In json & yaml, curlies need to be inside quotes to make sure they parse as
strings. Especially watch in .yaml, where { as the first character of a key or
value will throw a formatting error if it's not in quotes like this:
*"{key}"*

You can also reference keys nested deeper in the context hierarchy, in cases
where you have a dictionary that contains lists/dictionaries that might contain
other lists/dictionaries and so forth.

.. code-block:: yaml

  root:
    - list index 0
    - key1: this is a value from a dict containing a list, which contains a dict at index 1
      key2: key 2 value
    - list index 1

Given the context above, you can use formatting expressions to access nested
values like this:

.. code-block:: text

  '{root[0]}' == list index 0
  '{root[1][key1]}' == this is a value from a dict containing a list, which contains a dict at index 1
  '{root[1][key2]}' == key 2 value
  '{root[2]}' == list index 1


py strings
==========
py strings allow you to execute python expressions dynamically. This allows you
to use a python expression wherever you can use a string formatting expression.

A py string looks like this:

.. code-block:: text

  !py <<your python expression here>>


For example, if ``context['key']`` is 'abc', the following will return True:
``!py len(key) == 3"``

The Py string expression has the usual python builtins available to it, in
addition to the Context dictionary. In other words, you can use functions like
``abs``, ``len`` - full list here
https://docs.python.org/3/library/functions.html.

Notice that you can use the context keys directly as variables. Unlike string
formatting expressions, you don't surround the key name with {curlies}.

In pipeline yaml, if the first character of the py string is a yaml structural
character, you should put the Py string in quotes or as part of a literal block.

.. code-block:: yaml

  - name: pypyr.steps.echo
    description: don't run this step if int > 4.
                 No need to wrap the expression in extra quotes!
    run: !py thisIsAnInt < 5
    in:
      echoMe: you'll see me if context thisIsAnInt is less than 5.
  - name: pypyr.steps.echo
    description: only run this step if breakfast includes spam
                 since the first char is a single quote, wrap the Py string in
                 double quotes to prevent malformed yaml.
    run: !py "'spam' in ['eggs', 'spam', 'bacon']"
    in:
      echoMe: you should see me because spam is in breakfast!

See a worked example `for py strings here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/pystrings.yaml>`__.

sic strings
===========
If a string is NOT to have {substitutions} run on it, it's *sic erat scriptum*,
or *sic* for short. This is handy especially when you are dealing with json
as a string, rather than an actual json object, so you don't have to double
curly all the structural braces.

A *sic* string looks like this:

.. code-block:: text

  !sic <<your string literal here>>

For example:

.. code-block:: text

  !sic piping {key} the valleys wild

Will return "piping {key} the valleys wild" without attempting to substitute
{key} from context. You can happily use ", ' or {} inside a ``!sic my string``
string without escaping these any further. This makes sic strings ideal for
strings containing json.

You can surround the Sic string with single or double quotes like this
``!sic 'my string here'`` or ``!sic "my string here"``. This is handy if your
string starts with a yaml structural character like square [ or curly { braces.
Check example below for escape sequences if you do so.

.. code-block:: yaml

  - name: pypyr.steps.echo
    description: >
                use a sic string not to format any {values}. Do watch the
                use of the yaml literal with block chomping indicator |- to
                prevent the last character in the string from being a LF.
    in:
      echoMe: !sic |-

              {
                "key1": "key1 value with a {curly}"
              }
  - name: pypyr.steps.echo
    description: use a sic string not to format any {values} on one line. No need to escape further quotes.
    in:
      echoMe: !sic string with a {curly} with ", ' and & and double quote at end:"
  - name: pypyr.steps.echo
    description: use a sic string with single quotes.
    in:
      echoMe: !sic '{string} with {curlies} inside single quotes, : colon, quote ", backslash \.'
  - name: pypyr.steps.echo
    description: use a sic string with double quotes. Double up the backslashes!
    in:
      echoMe: !sic "[string] with {curlies} inside double quotes, : colon, quote \", backslash \\."


You can pick single or double quotes, so just go with whichever is less annoying
for your particular string.

See a worked example `for substitutions here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/substitutions.yaml>`__.

********
Plug-Ins
********
The pypyr core is deliberately kept light so the dependencies are down to the
minimum. I loathe installs where there\'re a raft of extra deps that I don\'t
use clogging up the system.

Where other libraries are requisite, you can selectively choose to add this
functionality by installing a pypyr plug-in.

+----------------------------+-------------------------------------------------+
| **boss pypyr plug-ins**    | **description**                                 |
+----------------------------+-------------------------------------------------+
| |pypyr-aws|                | Interact with the AWS sdk api. Supports all AWS |
|                            | Client functions, such as S3, EC2, ECS & co.    |
|                            | via the AWS low-level Client API.               |
+----------------------------+-------------------------------------------------+
| |pypyr-slack|              | Send messages to Slack                          |
+----------------------------+-------------------------------------------------+

*****
Help!
*****
Don't Panic! For help, community or talk, join the chat on |discord|!

**********
Contribute
**********
Developers
==========
For information on how to help with pypyr, run tests and coverage, please do
check out the `contribution guide <CONTRIBUTING.rst>`_.

Bugs
====
Well, you know. No one's perfect. Feel free to `create an issue
<https://github.com/pypyr/pypyr-cli/issues/new>`_.

**********
Thank yous
**********
pypyr is fortunate to stand on the shoulders of a giant in the shape of the
excellent `ruamel.yaml <https://pypi.org/project/ruamel.yaml>`_ library by
Anthon van der Neut for all yaml parsing and validation.

.. |build-status| image:: https://api.shippable.com/projects/58efdfe130eb380700e559a6/badge?branch=master
                    :alt: build status
                    :target: https://app.shippable.com/github/pypyr/pypyr-cli

.. |coverage| image:: https://api.shippable.com/projects/58efdfe130eb380700e559a6/coverageBadge?branch=master
                :alt: coverage status
                :target: https://app.shippable.com/github/pypyr/pypyr-cli

.. |pypi| image:: https://badge.fury.io/py/pypyr.svg
                :alt: pypi version
                :target: https://pypi.python.org/pypi/pypyr/
                :align: bottom

.. |pypyr-aws| replace:: `pypyr-aws <https://github.com/pypyr/pypyr-aws/>`__

.. |pypyr-slack| replace:: `pypyr-slack <https://github.com/pypyr/pypyr-slack/>`__

.. |discord| replace:: `discord <https://discordapp.com/invite/8353JkB>`__
