#!/usr/bin/env bash
# Tests and validates code, increment version, tag in git and commit, push to
# pypi.
# Run when git working directory clean.
# Don't use me if you've got a dir called .deployenv in $PWD that you want to
# keep.
# if something goes horribly wrong, get rid of git commit and tag like this:
# git reset --hard HEAD~1                        # rollback the commit
# git tag -d `git describe --tags --abbrev=0`    # delete the tag

remove_deployenv()
{
  echo "Virtual Environment name is: ${VIRTUAL_ENV}"
  if [ ${VIRTUAL_ENV} ] && [ "`basename ${VIRTUAL_ENV}`" = ".deployenv" ]; then
    # get rid of the virtual env
    echo "Removing virtualenv .deployenv"
    deactivate
    rm -rf .deployenv
  fi
}

abort()
{
    echo "An error occurred. Exiting..." >&2
    remove_deployenv
    exit 1
}

# If an error occurs, the abort() function will be called.
trap 'abort' 0

# stop on error, and treat unset vars as errors.
set -eu

# First, do a tox on stage - this flake8 lints the code, validates README rst,
# validates build. All good stuff before releasing.
tox -e stage -- tests

# do packaging inside a virtual env so this doesn't pollute global python scope.
virtualenv .deployenv
# virtualenv activate doesn't work with strict no unset vars mode
set +u
. .deployenv/bin/activate
set -u

# Bump version number. Use deploy switch on setup.py to install deploy deps.
pip install -e .[deploy]

# major, minor, patch

# all done, clean-up
remove_deployenv

# Done!
trap : 0
