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

Python version
==============
Tested against Python 3.6

*****
Usage
*****
Run your first pipeline
=======================
Run one of the built-in pipelines to get a feel for it:

.. code-block:: bash

  $ pypyr echo --context "echoMe=Ceci n'est pas une pipe"

You can achieve the same thing by running a pipeline where the context is set
in the pipeline yaml rather than as a --context argument:

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

  # run pipelines/mypipelinename.yaml with an input context. For this input to
  # be available to your pipeline you need to specify a context_parser in your
  # pipeline yaml.
  $ pypyr mypipelinename --context 'mykey=value'

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
A pipeline is a .yaml file. Save pipelines to a `pipelines` directory in your
working directory.

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
      in: #optional. In parameters are added to the context so that this step and subsequent steps can use these key-value pairs.
        parameter1: value1
        parameter2: value2

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
| donothing                   | Does what it says. Nothing.                     |`pypyr donothing`                                                                    |
|                             |                                                 |                                                                                     |
|                             |                                                 |                                                                                     |
|                             |                                                 |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| echo                        | Echos context value echoMe to output.           |`pypyr echo --context "echoMe=text goes here"`                                       |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyrversion                | Prints the python cli version number.           |`pypyr pypyrversion`                                                                 |
|                             |                                                 |                                                                                     |
|                             |                                                 |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| magritte                    | Thoughts about pipes.                           |`pypyr magritte`                                                                     |
|                             |                                                 |                                                                                     |
|                             |                                                 |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+

context_parser
==============
Optional.

A context_parser parses the pypyr --context input argument. The chances are
pretty good that it will take the --context argument and put in into the pypyr
context.

The pypyr context is a dictionary that is in scope for the duration of the entire
pipeline. The context_parser can initialize the context. Any step in the pipeline
can add, edit or remove items from the context dictionary.

Built-in context parsers
------------------------
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| **context parser**          | **description**                                 | **example input**                                                                   |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.commas         | Takes a comma delimited string and returns a    |`pypyr pipelinename --context "param1,param2,param3"`                                |
|                             | dictionary where each element becomes the key,  |                                                                                     |
|                             | with value to true.                             |This will create a context dictionary like this:                                     |
|                             |                                                 |{'param1': True, 'param2': True, 'param3': True}                                     |
|                             | Don't have spaces between commas unless you     |                                                                                     |
|                             | really mean it. \"k1=v1, k2=v2\" will result in |                                                                                     |
|                             | a context key name of \' k2\' not \'k2\'.       |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.json           | Takes a json string and returns a dictionary.   |`pypyr pipelinename --context \'{"key1":"value1","key2":"value2"}\'`                 |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.jsonfile       | Opens json file and returns a dictionary.       |`pypyr pipelinename --context \'./path/sample.json'`                                 |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.keyvaluepairs  | Takes a comma delimited key=value pair string   |`pypyr pipelinename --context "param1=value1,param2=value2,param3=value3"`           |
|                             | and returns a dictionary where each pair becomes|                                                                                     |
|                             | a dictionary element.                           |                                                                                     |
|                             |                                                 |                                                                                     |
|                             | Don't have spaces between commas unless you     |                                                                                     |
|                             | really mean it. \"k1=v1, k2=v2\" will result in |                                                                                     |
|                             | a context key name of \' k2\' not \'k2\'.       |                                                                                     |
+-----------------------------+-------------------------------------------------+-------------------------------------------------------------------------------------+
| pypyr.parser.yamlfile       | Opens a yaml file and writes the contents into  |`pypyr pipelinename --context \'./path/sample.yaml'`                                 |
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
      """This is the signature for a context parser. Input context is the string received from pypyr --context 'value here'"""
      assert context_arg, ("pipeline must be invoked with --context set.")
      logger.debug("starting")

      # your clever code here. Chances are pretty good you'll be doing things with the input context string to create a dictionary.

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


Built-in steps
--------------

+-------------------------------+-------------------------------------------------+------------------------------+
| **step**                      | **description**                                 | **input context properties** |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.contextclear`_   | Remove specified items from context.            | contextClear (list)          |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.contextclearall`_| Wipe the entire context.                        |                              |
|                               |                                                 |                              |
+-------------------------------+-------------------------------------------------+------------------------------+
| `pypyr.steps.contextset`_     | Sets context values from already existing       | contextSet (dict)            |
|                               | context values.                                 |                              |
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
| `pypyr.steps.py`_             | Executes the context value `pycode` as python   | pycode (string)              |
|                               | code.                                           |                              |
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


pypyr.steps.contextset
^^^^^^^^^^^^^^^^^^^^^^
Sets context values from already existing context values.

This is handy if you need to prepare certain keys in context where a next step
might need a specific key. If you already have the value in context, you can
create a new key (or update existing key) with that value.

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

  pypyr mypipeline --context "echoMe=Ceci n'est pas une pipe"


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

Values are strings to write to $ENV. You can use {key} substitutions to format
the string from context.
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
  - path-like. Path to file on disk. Can be relative.

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
  - path-like. Path to file on disk. Can be relative.

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

You can use context variable substitutions with curly braces. See a worked
example `for substitions here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/substitutions.yaml>`__.

Escape literal curly braces with doubles: {{ for {, }} for }


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

You can use context variable substitutions with curly braces. See a worked
example `for substitions here
<https://github.com/pypyr/pypyr-example/tree/master/pipelines/substitutions.yaml>`__.

Escape literal curly braces with doubles: {{ for {, }} for }

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

You can use {key} substitutions to format the string from context.

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

You can use {key} substitutions to format the string from context.

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

********
Plug-Ins
********
The pypyr core is deliberately kept light so the dependencies are down to the
minimum. I loathe installs where there\'re a raft of extra deps that I don\'t
use clogging up the system.

Where other libraries are requisite, you can selectively choose to add this
functionality by installing a pypyr plug-in.

.. tabularcolumns:: |l|l|
+----------------------------+-------------------------------------------------+
| **plug-in**                | **description**                                 |
+----------------------------+-------------------------------------------------+
| |pypyr-aws|                | Interact with the AWS sdk api. Supports all AWS |
|                            | Client functions, such as S3, EC2, ECS & co.    |
|                            | via the AWS low-level Client API.               |
+----------------------------+-------------------------------------------------+
| |pypyr-slack|              | Send messages to Slack                          |
+----------------------------+-------------------------------------------------+

**********************************
Testing (for pypyr-cli developers)
**********************************
Testing without worrying about dependencies
===========================================
Run tox to test the packaging cycle inside a virtual env, plus run all tests:

.. code-block:: bash

  # just run tests
  $ tox -e dev -- tests
  # run tests, validate README.rst, run flake8 linter
  $ tox -e stage -- tests

If tox takes too long
=====================
The test framework is pytest. If you only want to run tests:

.. code-block:: bash

  $ pip install -e .[dev,test]

Day-to-day testing
==================
- Tests live under */tests* (surprising, eh?). Mirror the directory structure of
  the code being tested.
- Prefix a test definition with *test_* - so a unit test looks like

  .. code-block:: python

    def test_this_should_totally_work():

- To execute tests, from root directory:

  .. code-block:: bash

    pytest tests

- For a bit more info on running tests:

  .. code-block:: bash

    pytest --verbose [path]

- To execute a specific test module:

  .. code-block:: bash

    pytest tests/unit/arb_test_file.py

**********
Contribute
**********
Bugs
====
Well, you know. No one's perfect. Feel free to `create an issue
<https://github.com/pypyr/pypyr-cli/issues/new>`_.

Contribute to the core cli
==========================
The usual jazz - create an issue, fork, code, test, PR. It might be an idea to
discuss your idea via the Issues list first before you go off and write a
huge amount of code - you never know, something might already be in the works,
or maybe it's not quite right for the core-cli (you're still welcome to fork
and go wild regardless, of course, it just mightn't get merged back in here).

Roll your own plug-in
=====================
You've probably noticed by now that pypyr is built to be pretty extensible.
You've probably also noticed that the core pypyr cli is deliberately kept light.
The core cli is philosophically only a way of running a sequence of steps.
Dependencies to external libraries should generally get their own package, so
end-users can selectively install what they need rather than have a monolithic
batteries-included application.

If you've got some custom context_parser or steps code that are useful, create a
repo and bask in the glow of sharing with the open source community. Honor the
pypyr Apache license please.

I generally name plug-ins `pypyr-myplugin`, where myplugin is likely some sort
of dependency that you don't want in the pypyr core cli. For example,
`pypyr-aws` contains pypyr-steps for the AWS boto3 library. This is kept separate
so that you don't have to deal with yet another dependency you don't need if your
current project isn't using AWS.

If you want your plug-in listed here for official cred, please get in touch via
the Issues list. Get in touch anyway, would love to hear from you at
https://www.345.systems/contact.

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
