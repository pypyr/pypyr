#####################
Contributing to pypyr
#####################
pypyr is open source. Your contributions are most welcome.

.. contents::

.. section-numbering::

**********
Contribute
**********
Feel free to join pypyr on |discord|.

Bugs
====
Well, you know. No one's perfect. Feel free to `create an issue
<https://github.com/pypyr/pypyr-cli/issues/new>`_.

Contribute to the core cli
==========================
The usual jazz - create an issue, fork, code, test, PR. It might be an idea to
discuss your idea on discord or via the Issues list first before you go off and
write a huge amount of code - you never know, something might already be in the
works, or maybe it's not quite right for the core-cli (you're still welcome to
fork and go wild regardless, of course, it just mightn't get merged back in
here).

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
the Issues list. Get in touch anyway, would love to hear from you on |discord|
or at https://www.345.systems/contact.

*****************
Developer's Guide
*****************
Coding Style
============
You've read `pep8 <https://www.python.org/dev/peps/pep-0008/>`__? pypyr uses flake8 as a
quality gate during ci.

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

Coverage
========
pypyr has 100% test coverage. Shippable CI enforces this on all branches.

.. code-block:: bash

  # run coverage tests with terminal output
  tox -e ci -- --cov=pypyr --cov-report term tests


PRs
===
When you pull request, code will have to pass the linting and coverage
requirements listed above. The CI enforces these, so might as well run these
locally first, eh?

Try to keep the commit history tidy.

The PR description should describe the changes in it. Favor concise bullets
over paragraphs. Chances are pretty good each bullet will coincide somewhat
with each commit included in the PR. Do use previous PRs as a guide.


.. |discord| replace:: `discord <https://discordapp.com/invite/8353JkB>`__
