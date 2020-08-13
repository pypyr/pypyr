.. image:: https://pypyr.io/images/2x1/pypyr-taskrunner-yaml-pipeline-automation-1200x600.1bd2401e4f8071d85bcb1301128e4717f0f54a278e91c9c350051191de9d22c0.png
    :alt: pypyr task runner for automation pipelines
    :align: center

#################
pypyr task runner
#################

All documentation is here: https://pypyr.io/

*pypyr*
    pronounce how you like, but I generally say *piper* as in "piping down the
    valleys wild"

pypyr is a free & open-source task-runner that lets you define and run 
sequential steps in a pipeline.

Like a turbo-charged shell script, but less finicky. Less annoying than a 
makefile.

pypyr runs pipelines defined in yaml. A pipeline is pretty much anything you 
want to automate with a sequence of steps. 

Automate anything by combining commands, different scripts in different 
languages & applications into one pipeline process.

You can run loops, conditionally execute steps based on conditions you specify,
wait for status changes before continuing, break on failure conditions or
swallow errors. Pretty useful for orchestrating continuous integration,
continuous deployment & devops operations.

pypyr gives you simple variable substitution & configuration file management so 
you can read, merge and write configuration files to and from yaml, json or 
just text.

|build-status| |coverage| |pypi|

.. contents::
  :local:

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

You can use the 
`official pypyr docker image <https://hub.docker.com/r/pypyr/pypyr/>`_ as a 
drop-in replacement for the pypyr executable.

.. code-block:: bash

  $ docker run pypyr/pypyr echo "Ceci n'est pas une pipe"


*****
Usage
*****
This is a pipeline
==================
Example pipeline that runs a sequence of steps and takes an optional custom 
cli input argument:

.. code-block:: yaml

  # ./show-me-what-you-got.yaml
  context_parser: pypyr.parser.keyvaluepairs
  steps:
    - name: pypyr.steps.echo
      in:
        echoMe: o hai!
    - name: pypyr.steps.cmd
      in:
        cmd: echo any cmd you like
    - name: pypyr.steps.shell
      in:
        cmd: echo ninja shell power | grep '^ninja.*r$' 
    - name: pypyr.steps.py
      in:
        pycode: print('any python you like')
    - name: pypyr.steps.cmd
      while:
        max: 3
      in:
        cmd: echo gimme a {whileCounter}
    - name: pypyr.steps.cmd
      foreach: [once, twice, thrice]
      in:
        cmd: echo say {i}
    - name: pypyr.steps.default
      in:
        defaults:
          sayBye: False
    - name: pypyr.steps.echo
      run: '{sayBye}'
      in:
        echoMe: k bye!


This is how you run a pipeline
==============================
This is what happens when you run this pipeline:

.. code-block:: bash

  $ pypyr show-me-what-you-got
  o hai!
  any cmd you like
  ninja shell power
  any python you like
  gimme a 1
  gimme a 2
  gimme a 3
  say once
  say twice
  say thrice

  $ pypyr show-me-what-you-got sayBye=true  
  o hai!
  any cmd you like
  ninja shell power
  any python you like
  gimme a 1
  gimme a 2
  gimme a 3
  say once
  say twice
  say thrice
  k bye!

*****
Help!
*****
Don't Panic! Check the `pypyr technical docs <https://pypyr.io/docs/>`_ to 
begin. For help, community & talk, check 
`pypyr twitter <https://twitter.com/pypyrpipes/>`_, or join the chat on 
|discord|!

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
<https://github.com/pypyr/pypyr/issues/new>`_.

*******
License
*******
pypyr is free & open-source software distributed under the Apache License.

Please see `LICENSE file <LICENSE>`_.

Copyright 2017 the pypyr contributors.
    

.. |build-status| image:: https://api.shippable.com/projects/58efdfe130eb380700e559a6/badge?branch=master
                    :alt: build status
                    :target: https://app.shippable.com/github/pypyr/pypyr/

.. |coverage| image:: https://api.shippable.com/projects/58efdfe130eb380700e559a6/coverageBadge?branch=master
                :alt: coverage status
                :target: https://app.shippable.com/github/pypyr/pypyr/

.. |pypi| image:: https://badge.fury.io/py/pypyr.svg
                :alt: pypi version
                :target: https://pypi.python.org/pypi/pypyr/
                :align: bottom

.. |discord| replace:: `discord <https://discordapp.com/invite/8353JkB>`__
