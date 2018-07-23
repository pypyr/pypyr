#########################
pypyr cli pipeline runner
#########################

.. image:: https://cdn.345.systems/wp-content/uploads/2017/03/pypyr-logo-small.png
    :alt: pypyr-logo
    :align: left

*pypyr*
    pronounce how you like, but I generally say *piper* as in "piping down the
    valleys wild"


pypyr is a command line interface to run pipelines defined in yaml. Think of
pypyr as a simple task runner that lets you run sequential steps.

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
Tested against Python 3.6

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
pypyr assumes a pipelines directory in your current working directory.

.. code-block:: bash

  # run pipelines/mypipelinename.yaml with DEBUG logging level
  $ pypyr mypipelinename --log 10

  # run pipelines/mypipelinename.yaml with INFO logging level.
  $ pypyr mypipelinename --log 20

  # If you don't specify --log it defaults to 20 - INFO logging level.
  $ pypyr mypipelinename

  # run pipelines/mypipelinename.yaml. The 2nd argument is any arbitrary string,
  # known as the input context argument. For this input argument to be available
  # to your pipeline you need to specify a context parser in your pipeline yaml.
  $ pypyr mypipelinename arbitrary_string_here

  # run pipelines/mypipelinename.yaml with an input context in key-value
  # pair format. For this input to be available to your pipeline you need to
  # specify a context_parser like pypyr.parser.keyvaluepairs in your
  # pipeline yaml.
  $ pypyr mypipelinename "mykey=value"

Get cli help
============
pypyr has a couple of arguments and switches you might find useful. See them all
here:

.. code-block:: bash

  $ pypyr -h

Examples
========
If you prefer reading code to reading words, https://github.com/pypyr/pypyr-example

***************************
Anatomy of a pypyr pipeline
***************************
Pipeline yaml structure
=======================
A pipeline is a .yaml file. pypyr uses YAML version 1.2.

Save pipelines to a `pipelines` directory in your working directory.

.. code-block:: yaml

  # This is an example showing the anatomy of a pypyr pipeline
  # A pipeline should be saved as {working dir}/pipelines/mypipelinename.yaml.
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
| echo                        | Echos context value echoMe to output.           |``pypyr echo "text goes here"``                                                      |
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

A context_parser parses the pypyr command's context input argument. This is the
second positional argument from the command line.

The chances are pretty good that the context_parser will take the context
command argument and put in into the pypyr context.

The pypyr context is a dictionary that is in scope for the duration of the entire
pipeline. The context_parser can initialize the context. Any step in the pipeline
can add, edit or remove items from the context dictionary.

Built-in context parsers
------------------------
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| **context parser**          | **description**                                 | **example input**                                                                   |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.commas         | Takes a comma delimited string and returns a    |``pypyr pipelinename "param1,param2,param3"``                                        |
|                             | dictionary where each element becomes the key,  |                                                                                     |
|                             | with value to true.                             |This will create a context dictionary like this:                                     |
|                             |                                                 |{'param1': True, 'param2': True, 'param3': True}                                     |
|                             | Don't have spaces between commas unless you     |                                                                                     |
|                             | really mean it. \"k1=v1, k2=v2\" will result in |                                                                                     |
|                             | a context key name of \' k2\' not \'k2\'.       |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.json           | Takes a json string and returns a dictionary.   |``pypyr pipelinename '{"key1":"value1","key2":"value2"}'``                           |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.jsonfile       | Opens json file and returns a dictionary.       |``pypyr pipelinename "./path/sample.json"``                                          |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.keyvaluepairs  | Takes a comma delimited key=value pair string   |``pypyr pipelinename "param1=value1,param2=value2,param3=value3"``                   |
|                             | and returns a dictionary where each pair becomes|                                                                                     |
|                             | a dictionary element.                           |                                                                                     |
|                             |                                                 |                                                                                     |
|                             | Don't have spaces between commas unless you     |                                                                                     |
|                             | really mean it. \"k1=v1, k2=v2\" will result in |                                                                                     |
|                             | a context key name of \' k2\' not \'k2\'.       |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.list           | Takes a comma delimited string and returns a    |``pypyr pipelinename "param1,param2,param3"``                                        |
|                             | list in context with name *argList*.            |                                                                                     |
|                             |                                                 |This will create a context dictionary like this:                                     |
|                             | Don't have spaces between commas unless you     |{'argList': ['param1', 'param2', 'param3']}                                          |
|                             | really mean it. \"v1, v2\" will result in       |                                                                                     |
|                             | argList[1] being \' v2\' not \'v2\'.            |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.string         | Takes any arbitrary string and returns a        |``pypyr pipelinename "arbitrary string here"``                                       |
|                             | string in context with name *argString*.        |                                                                                     |
|                             |                                                 |This will create a context dictionary like this:                                     |
|                             |                                                 |{'argString': 'arbitrary string here'}                                               |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.yamlfile       | Opens a yaml file and writes the contents into  |``pypyr pipelinename "./path/sample.yaml"``                                          |
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


  def get_parsed_context(context_arg):
      """This is the signature for a context parser.

      Args:
        context_arg: string. Passed from command-line invocation where
                     pypyr pipelinename 'this is the context_arg'

      Returns:
        dict. This dict will initialize the context for the pipeline run.
      """
      assert context_arg, ("pipeline must be invoked with context set.")
      logger.debug("starting")

      # your clever code here. Chances are pretty good you'll be doing things
      # with the input context_arg string to create a dictionary.

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
          description: Optional Description is for humans. It's any yaml-escaped text that makes your life easier.
          in: #optional. In parameters are added to the context so that this step and subsequent steps can use these key-value pairs.
            parameter1: value1
            parameter2: value2


* You can freely mix and match simple and complex steps in the same pipeline.

* Frankly, the only reason simple steps are there is because I'm lazy and I dislike redundant typing.

Step decorators
---------------

Complex steps have various optional step decorators that change how or if a step is run.

Don't bother specifying these unless you want to deviate from the default values.


.. code-block:: yaml

  steps:
    - name: my.package.another.module
      description: Optional Description is for humans. It's any yaml-escaped text that makes your life easier.
      in: # optional. In parameters are added to the context so that this step and subsequent steps can use these key-value pairs.
        parameter1: value1
        parameter2: value2
      foreach: [] # optional. Repeat the step once for each item in this list. By default step executes once.
      run: True # optional. Runs this step if True, skips step if False. Defaults to True if not specified.
      skip: False # optional. Skips this step if True, runs step if False. Defaults to False if not specified.
      swallow: False # optional. Swallows any errors raised by the step. Defaults to False if not specified.

+---------------+----------+---------------------------------------------+----------------+
| **decorator** | **type** | **description**                             | **default**    |
+---------------+----------+---------------------------------------------+----------------+
| foreach       | list     | Run the step once for each item in the list.| None           |
|               |          | The iterator is context['i'].               |                |
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

All step decorators support `Substitutions`_.

Note that for all bool values, the standard Python truth value testing rules apply.
https://docs.python.org/3/library/stdtypes.html#truth-value-testing

Simply put, this means that 1, TRUE, True and true will be True.

None/Empty, 0,'', [], {} will be False.

See a worked example for `step decorators here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/stepdecorators.yaml>`__.

See a worked example of the looping `foreach decorator here
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/foreach.yaml>`__.

Here is an example of `foreach dynamic decorator evaluation
<https://github.com/pypyr/pypyr-example/blob/master/pipelines/foreachconditionals.yaml>`__.


Built-in steps
--------------

+-------------------------------+-------------------------------------------------+------------------------------+
| **step**                      | **description**                                 | **input context properties** |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.assert`_         | Stop pipeline if item in context is not as      | assertThis (any)             |
|                               | expected.                                       | assertEquals (any)           |
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
| `pypyr.steps.default`_        | Set default values in context. Only set values  | defaults (dict)              |
|                               | if they do not exist already.                   |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.echo`_           | Echo the context value `echoMe` to the output.  | echoMe (string)              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.env`_            | Get, set or unset $ENVs.                        | envGet (dict)                |
|                               |                                                 |                              |
|                               |                                                 | envSet (dict)                |
|                               |                                                 |                              |
|                               |                                                 | envUnset (list)              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.fetchjson`_      | Loads json file into pypyr context.             | fetchJsonPath (path-like)    |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.fetchyaml`_      | Loads yaml file into pypyr context.             | fetchYamlPath (path-like)    |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.fileformat`_     | Parse file and substitute {tokens} from         | fileFormatIn (path-like)     |
|                               | context.                                        |                              |
|                               |                                                 | fileFormatOut (path-like)    |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.fileformatjson`_ | Parse json file and substitute {tokens} from    | fileFormatJsonIn (path-like) |
|                               | context.                                        |                              |
|                               |                                                 | fileFormatJsonOut (path-like)|
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.fileformatyaml`_ | Parse yaml file and substitute {tokens} from    | fileFormatYamlIn (path-like) |
|                               | context.                                        |                              |
|                               |                                                 | fileFormatYamlOut (path-like)|
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.filereplace`_    | Parse input file and replace search strings.    | fileReplaceIn (path-like)    |
|                               |                                                 |                              |
|                               |                                                 | fileReplaceOut (path-like)   |
|                               |                                                 |                              |
|                               |                                                 | fileReplacePairs (dict)      |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.py`_             | Executes the context value `pycode` as python   | pycode (string)              |
|                               | code.                                           |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.pype`_           | Run another pipeline from within the current    | pype (dict)                  |
|                               | pipeline.                                       |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.pypyrversion`_   | Writes installed pypyr version to output.       |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.safeshell`_      | Runs the program and args specified in the      | cmd (string)                 |
|                               | context value `cmd` as a subprocess.            |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.shell`_          | Runs the context value `cmd` in the default     | cmd (string)                 |
|                               | shell. Use for pipes, wildcards, $ENVs, ~       |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.tar`_            | Archive and/or extract tars with or without     | tarExtract (dict)            |
|                               | compression. Supports gzip, bzip2, lzma.        |                              |
|                               |                                                 | tarArchive (dict)            |
+-------------------------------+-------------------------------------------------+------------------------------+

pypyr.steps.assert
^^^^^^^^^^^^^^^^^^
Assert that something is True or equal to something else.

Uses these context keys:

- ``assertThis``

  - mandatory
  - If assertEquals not specified, evaluates as a boolean.

- ``assertEquals``

  - optional
  - If specified, compares ``assertThis`` to ``assertEquals``

If ``assertThis`` evaluates to False raises error.

If ``assertEquals`` is specified, raises error if ``assertThis != assertEquals``.

Supports `Substitutions`_.

Examples:

.. code-block:: yaml

    # continue pipeline
    assertThis: True
    # stop pipeline
    assertThis: False

or with substitutions:

.. code-block:: yaml

    interestingValue: True
    assertThis: '{interestingValue}' # continue with pipeline

Non-0 numbers evalute to True:

.. code-block:: yaml

    assertThis: 1 # non-0 numbers assert to True. continue with pipeline

String equality:

.. code-block:: yaml

    assertThis: 'up the valleys wild'
    assertEquals: 'down the valleys wild' # strings not equal. stop pipeline.

String equality with substitutions:

.. code-block:: yaml

    k1: 'down'
    k2: 'down'
    assertThis: '{k1} the valleys wild'
    assertEquals: '{k2} the valleys wild' # substituted strings equal. continue pipeline.


Number equality:

.. code-block:: yaml

    assertThis: 123.45
    assertEquals: 123.45 # numbers equal. continue with pipeline.

Number equality with substitutions:

.. code-block:: yaml

    numberOne: 123.45
    numberTwo: 678.9
    assertThis: '{numberOne}'
    assertEquals: '{numberTwo}' # substituted numbers not equal. Stop pipeline.

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
  assertThis: '{complexOne}'
  assertEquals: '{complexTwo}' # substituted types equal. Continue pipeline.


See a worked example `for assert here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/assert.yaml>`__.

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

  contextsetf:
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

See a worked example `for contextsetf here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/contextset.yaml>`__.

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

At least one of these context keys must exist:

- envGet
- envSet
- envUnset

This step will run whatever combination of Get, Set and Unset you specify.
Regardless of combination, execution order is Get, Set, Unset.

See a worked example `for environment variables here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/env_variables.yaml>`__.

envGet
""""""
Get $ENVs into the pypyr context.

``context['envGet']`` must exist. It's a dictionary.

Values are the names of the $ENVs to write to the pypyr context.

Keys are the pypyr context item to which to write the $ENV values.

For example, say input context is:

.. code-block:: yaml

  key1: value1
  key2: value2
  pypyrCurrentDir: value3
  envGet:
    pypyrUser: USER
    pypyrCurrentDir: PWD


This will result in context:

.. code-block:: yaml

  key1: value1
  key2: value2
  key3: value3
  pypyrCurrentDir: <<value of $PWD here, not value3>>
  pypyrUser: <<value of $USER here>>

envSet
""""""
Set $ENVs from the pypyr context.

``context['envSet']`` must exist. It's a dictionary.

Values are strings to write to $ENV. You can use {key} `Substitutions`_ to
format the string from context.
Keys are the names of the $ENV values to which to write.

For example, say input context is:

.. code-block:: yaml

  key1: value1
  key2: value2
  key3: value3
  envSet:
      MYVAR1: {key1}
      MYVAR2: before_{key3}_after
      MYVAR3: arbtexthere

This will result in the following $ENVs:

.. code-block:: yaml

  $MYVAR1 = value1
  $MYVAR2 = before_value3_after
  $MYVAR3 = arbtexthere

Note that the $ENVs are not persisted system-wide, they only exist for the
pypyr sub-processes, and as such for the subsequent steps during this pypyr
pipeline execution. If you set an $ENV here, don't expect to see it in your
system environment variables after the pipeline finishes running.

envUnset
""""""""
Unset $ENVs.

Context is a dictionary or dictionary-like. context is mandatory.

``context['envUnset']`` must exist. It's a list.
List items are the names of the $ENV values to unset.

For example, say input context is:

.. code-block:: yaml

    key1: value1
    key2: value2
    key3: value3
    envUnset:
        MYVAR1
        MYVAR2

This will result in the following $ENVs being unset:

.. code-block:: bash

  $MYVAR1
  $MYVAR2

pypyr.steps.fetchjson
^^^^^^^^^^^^^^^^^^^^^
Loads a json file into the pypyr context.

This step requires the following key in the pypyr context to succeed:

- fetchJsonPath.
  - path-like. Path to file on disk. Can be relative. Supports `Substitutions`_.

Json parsed from the file will be merged into the pypyr context. This will
overwrite existing values if the same keys are already in there.

I.e if file json has ``{'eggs' : 'boiled'}``, but context ``{'eggs': 'fried'}``
already exists, returned ``context['eggs']`` will be 'boiled'.

The json should not be an array [] at the top level, but rather an Object.

pypyr.steps.fetchyaml
^^^^^^^^^^^^^^^^^^^^^
Loads a yaml file into the pypyr context.

This step requires the following key in the pypyr context to succeed:

- fetchYamlPath.
  - path-like. Path to file on disk. Can be relative. Supports `Substitutions`_.

Yaml parsed from the file will be merged into the pypyr context. This will
overwrite existing values if the same keys are already in there.

I.e if file yaml has

.. code-block:: yaml

  eggs: boiled

but context ``{'eggs': 'fried'}`` already exists, returned ``context['eggs']``
will be 'boiled'.

The yaml should not be a list at the top level, but rather a mapping.

So the top-level yaml should not look like this:

.. code-block:: yaml

  - eggs
  - ham

but rather like this:

.. code-block:: yaml

  breakfastOfChampions:
    - eggs
    - ham


pypyr.steps.fileformat
^^^^^^^^^^^^^^^^^^^^^^
Parses input text file and substitutes {tokens} in the text of the file
from the pypyr context.

The following context keys expected:

- fileFormatIn

  - Path to source file on disk.

- fileFormatOut

  - Write output file to here. Will create directories in path if these do not
    exist already.

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

The file in and out paths support `Substitutions`_.

pypyr.steps.fileformatjson
^^^^^^^^^^^^^^^^^^^^^^^^^^
Parses input json file and substitutes {tokens} from the pypyr context.

Pretty much does the same thing as `pypyr.steps.fileformat`_, only it makes it
easier to work with curly braces for substitutions without tripping over the
json's structural braces.

The following context keys expected:

- fileFormatJsonIn

  - Path to source file on disk.

- fileFormatJsonOut

  - Write output file to here. Will create directories in path if these do not
    exist already.

`Substitutions`_ enabled for keys and values in the source json.

The file in and out paths also support `Substitutions`_.

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

- fileFormatYamlIn

  - Path to source file on disk.

- fileFormatYamlOut

  - Write output file to here. Will create directories in path if these do not
    exist already.

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

- fileReplaceIn

  - Path to source file on disk.

- fileReplaceOut

  - Write output file to here. Will create directories in path if these do not
    exist already.

- fileReplacePairs

  - dictionary where format is:

    - 'find_string': 'replace_string'

Example input context:

.. code-block:: yaml

  fileReplaceIn: ./infile.txt
  fileReplaceOut: ./outfile.txt
  fileReplacePairs:
    findmestring: replacewithme
    findanotherstring: replacewithanotherstring
    alaststring: alastreplacement

This also does string substitutions from context on the fileReplacePairs. It
does this before it search & replaces the *fileReplaceIn* file.

Be careful of order. The last string replacement expression could well replace
a replacement that an earlier replacement made in the sequence.

If fileReplacePairs is not an ordered collection,
replacements could evaluate in any given order. If you are creating your *in*
parameters in the pipeline yaml, don't worry about it, it will be an ordered
dictionary already, so life is good.

The file in and out paths support `Substitutions`_.

See a worked
`example here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/filereplace.yaml>`_.

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
    pipeArg: 'argument here' # optional. string.
    raiseError: True # optional. bool. Defaults True.
    skipParse: True # optional. bool. Defaults True.
    useParentContext: True  # optional. bool. Defaults True.

+-----------------------+------------------------------------------------------+
| **pype property**     | **description**                                      |
+-----------------------+------------------------------------------------------+
| name                  | Name of child pipeline to execute. This {name}.yaml  |
|                       | must exist in the *working directory/pipelines* dir. |
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

.. code-block:: bash

    steps:
      - pypyr.steps.pypyrversion

pypyr.steps.safeshell
^^^^^^^^^^^^^^^^^^^^^
Runs the context value `cmd` as a sub-process.

In `safeshell`, you cannot use things like exit, return, shell pipes, filename
wildcards, environment variable expansion, and expansion of ~ to a user’s
home directory. Use pypyr.steps.shell for this instead. Safeshell runs a
program, it does not invoke the shell.

Supports string `Substitutions`_.

Example pipeline yaml:

.. code-block:: bash

  steps:
    - name: pypyr.steps.safeshell
      in:
        cmd: ls -a

See a worked example `for shell power here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/shell.yaml>`__.

pypyr.steps.shell
^^^^^^^^^^^^^^^^^
Runs the context value `cmd` in the default shell. On a sensible O/S, this is
`/bin/sh`

Do all the things you can't do with `safeshell`.

Friendly reminder of the difference between separating your commands with ; or
&&:

- ; will continue to the next statement even if the previous command errored.
  It won't exit with an error code if it wasn't the last statement.
- && stops and exits reporting error on first error.

Supports string `Substitutions`_.

Example pipeline yaml using a pipe:

.. code-block:: bash

  steps:
    - name: pypyr.steps.shell
      in:
        cmd: ls | grep pipe; echo if you had something pipey it should show up;

See a worked example `for shell power here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/shell.yaml>`__.

pypyr.steps.tar
^^^^^^^^^^^^^^^
Archive and/or extract tars with or without compression.

At least one of these context keys must exist:

- tarExtract
- tarArchive

Optionally, you can also specify the tar compression format with
``context['tarFormat']``. If not specified, defaults to *lzma/xz*
Available options:

- '' - no compression
- gz (gzip)
- bz2 (bzip2)
- xz (lzma)

This step will run whatever combination of Extract and Archive you specify.
Regardless of combination, execution order is Extract, Archive.

Never extract archives from untrusted sources without prior inspection. It is
possible that files are created outside of path, e.g. members that have
absolute filenames starting with "/" or filenames with two dots "..".

See a worked example `for tar here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/tar.yaml>`__.

tarExtract
""""""""""
``context['tarExtract']`` must exist. It's a dictionary.

keys are the path to the tar to extract.

values are the destination paths.

You can use {key} substitutions to format the string from context. See
`Substitutions`_.

.. code-block:: yaml

  key1: here
  key2: tar.xz
  tarExtract:
    - in: path/to/my.tar.xz
      out: /path/extract/{key1}
    - in: another/{key2}
      out: .

This will:

- Extract *path/to/my.tar.xz* to */path/extract/here*
- Extract *another/tar.xz* to the current execution directory

  - This is the directory you're running pypyr from, not the pypyr pipeline
    working directory you set with the ``--dir`` flag.

tarArchive
""""""""""
``context['tarArchive']`` must exist. It's a dictionary.

keys are the paths to archive.

values are the destination output paths.

You can use {key} substitutions to format the string from context. See
`Substitutions`_.

.. code-block:: yaml

  key1: destination.tar.xz
  key2: value2
  tarArchive:
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

  '{root[0]}' = list index 0
  '{root[1][key1]}' = this is a value from a dict containing a list, which contains a dict at index 1
  '{root[1][key2]}' = key 2 value
  '{root[2]}' = list index 1


sic strings
===========
If a string is NOT to have {substitutions} run on it, it's *sic erat scriptum*,
or *sic* for short. This is handy especially when you are dealing with json
as a string, rather than an actual json object, so you don't have to double
curly all the structural braces.

A *sic* string looks like this:

.. code-block:: text

  [sic]"<<your string literal here>>"

For example:

.. code-block:: text

  [sic]"piping {key} the valleys wild"

Will return "piping {key} the valleys wild" without attempting to substitute
{key} from context. You can happily use ", ' or {} inside a ``[sic]""`` string
without escaping these any further. This makes sic strings ideal for strings
containing json.

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
| | **boss pypyr plug-ins**  | **description**                                 |
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
