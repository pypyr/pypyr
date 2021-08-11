========================
CI/CD tools using invoke
========================
This directory (+ ../tasks.py + ../invoke.yaml) contain experimental implementation of the same 
pipelines as pypyr uses for it's own build, but using invoke_.

The idea is to implement all, what is in ops/*.yaml files in pure invoke. This
shall allow to compare pypyr to invoke tooling.

.. _invoke: http://docs.pyinvoke.org/en/stable/


Prerequisities
==============
It expects required tools to be available. Most of the tools can be installed
globally in the system as they can be used as any other CLI.

These tools include:
- invoke
- flake8
- twine
- pytest (must be instaleled within virtualenv)
- codecov (must be probably instaleled within virtualenv)

Installation
============
Ensure all the CLI tools are installed.

Currently we expect invoke to be part of virtual env.

Configuration
=============
See file `invoke.yaml`

If you want to use private pypi, such as devpi-server, set env vars for twine and pip, e.g.::

  export TWINE_REPOSITORY_URL=http://10.0.0.1:3141/username/dev
  export TWINE_USERNAME=username
  export TWINE_PASSWORD=somepassword
  export PIP_INDEX_URL=$TWINE_REPOSITORY_URL

Usage
=====
To list all available invoke tasks::

  $ inv -l
  Available tasks:

    config                  Complete and validate needed cfg.
    package                 Run all package build tasks.
    pipeline-buildout       Lint and test.
    lint.all                Run all lint tasks.
    lint.flake8             flake8 linting.
    lint.setup-meta         Verify setup.py metadata.
    publish.all             Publish built packages to (public or private) pypi.
    test.all                Run all CI/CD either in local or remote (CI/CD
                            server) mode.
    test.codecov            Coverage (possibly with result upload).
    test.test-to-file       tests, output to file.
    test.test-to-terminal   tests, output to terminal with line nos.

To show help for particular task, e.g. for `lint.flake8`::

  inv lint.flake8 --help
  Usage: inv[oke] [--core-opts] lint.flake8 [other tasks here ...]

  Docstring:
    flake8 linting.

  Options:
    none

To call particular task, e.g. lint.flake8::

  $ inv lint.flake8
  ==> ops.lint.flake8: flake8 linting.
  <==: OK (ops.lint.flake8)


To run complete pipeline such as `pipeline-buidout`::

  $ inv pipeline-buildout
  ==> ops.lint.all: Run all lint tasks.
  ==> ops.lint.setup_meta: Verify setup.py metadata.
  running check
  <==: OK (ops.lint.setup_meta)
  ==> ops.lint.flake8: flake8 linting.
  <==: OK (ops.lint.flake8)
  <==: OK (ops.lint.all)
  ==> ops.config.all: Complete and validate needed cfg.
  <==: OK (ops.config.all)
  ==> ops.test.all: Run all CI/CD either in local or remote (CI/CD server) mode.
  ==> ops.test.test_to_terminal: tests, output to terminal with line nos.
  ============================= test session starts ==============================
  platform linux -- Python 3.9.1, pytest-6.2.4, py-1.10.0, pluggy-0.13.1
  rootdir: /home/javl/sandbox/pypyr/github-repo/pypyr, configfile: tox.ini
  plugins: cov-2.12.1
  collected 1157 items

  tests/integration/pypyr/errorhandling_int_test.py ................       [  1%]
  tests/integration/pypyr/pipelinerunner_int_test.py ..............        [  2%]
  tests/integration/pypyr/call/loopcallnested_int_test.py ..........       [  3%]
  tests/integration/pypyr/jump/loopjumpnested_int_test.py .                [  3%]
  tests/unit/pypyr/__main__test.py .                                       [  8%]
  tests/unit/pypyr/cli_test.py .................                           [ 10%]
  .....(truncated)....
  tests/unit/pypyr/utils/asserts_test.py .............                     [ 97%]
  tests/unit/pypyr/utils/filesystem_test.py .......                        [ 98%]
  tests/unit/pypyr/utils/poll_test.py ..............                       [ 99%]
  tests/unit/pypyr/utils/types_test.py .......                             [100%]

  ----------- coverage: platform linux, python 3.9.1-final-0 -----------
  Name    Stmts   Miss Branch BrPart  Cover   Missing
  ---------------------------------------------------
  ---------------------------------------------------
  TOTAL    2350      0    639      0   100%

  82 files skipped due to complete coverage.

  Required test coverage of 100.0% reached. Total coverage: 100.00%

  ============================= 1157 passed in 9.73s =============================
  <==: OK (ops.test.test_to_terminal)
  <==: OK (ops.test.all)
  ==> tasks.pipeline_buildout: Lint and test.
  <==: OK (tasks.pipeline_buildout)

Challenges
==========
Can we minimize installing dependencies of these tools into actual python
virtual env used for the package?

Invoke lessons learned
======================

Easy access to particular tasks
-------------------------------
The::

  $ inv -l

provides nice task listing + it allows to pick any of them and call as developer needs.

Tasks to be called independently
--------------------------------
If any tasks shall be called independently, it must be defined as separate `@task`.

Grouping (sub) tasks into single task shorten the code
------------------------------------------------------
In many cases there is no need to have independent task for each call to a CLI.

Putting multiple calls into single `@task` makes code shorter and simpler to read.

To make these sub-steps better visible in output, use `ops.step` to print what is goning on::

  from ops import step


  @task
  def magic(c):
      step("get magic stick")
      stick = get_magic_stick("wooden one")

      step("do the magic")
      stick.do_the_magic("now")

The `step` will produce lines such as::

  --> get magic stick
  --> do the magic

Fixing invoke limited task reporting on output
----------------------------------------------
By default, invoke prints something to stdout, but often it is not clear, which task was started and how it finished.

For this reason, `MyTask` class was added (see `ops/__init__.py`) which extends `__call__` to do some handy printing.

invoke.call causes forgotten pre-tasks runs
-------------------------------------------
One can call another task directly, e.g.::

  from invoke import call
  from . import othertasks

  @task
  def lint(c):
      call(othertasks.checkmeta).task(c)

However - if the othertasks.checkmeta declares some pre-tasks to be run, the `call` ignores them.

To run the pre-tasks, do declare the task `othertasks.checketa` as pre-task, e.g.::

  from invoke import call
  from . import othertasks

  @task(othertasks.checkmeta)
  def lint(c):
    pass

`invoke.task` is not easy to decorate or modify
-----------------------------------------------
The idea was to replace `@task(klass=MyTask)` by easier to use `@mytask`.

However, it turns out that the `invoke.task` decorator is not easy to decorate or to use with `functools.partial`.


