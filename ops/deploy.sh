#!/usr/bin/env bash
# Tests and validates code, increment version, tag in git and commit, push to
# pypi.
# Usage:
# Run when git working directory clean.
# run like so: ./ops/deploy.sh [bumplevel]
# where bumplevel either: major, minor, patch
# if you don't set bumplevel it defaults to patch.
# Don't use me if you've got a dir called .deployenv in $PWD that you want to
# keep.
# if something goes horribly wrong, get rid of git commit and tag like this:
# git reset --hard HEAD~1                        # rollback the commit
# git tag -d `git describe --tags --abbrev=0`    # delete the tag

# default BUMPLEVEL to patch if it doesn't exist.
set ${BUMPLEVEL} = ${BUMPLEVEL:=patch}
echo "Bumping (major.minor.patch): ${BUMPLEVEL}"

# take one parameter: name of virtual environment
create_virtualenv()
{
  echo "Creating virtual environment name is: ${1}"
  virtualenv ${1}
  # virtualenv activate doesn't work with strict no unset vars mode
  set +u
  . ${1}/bin/activate
  set -u
}

# take one parameter: name of virtual environment
remove_virtualenv()
{
  echo "removing virtual env ${1} if it exists."
  if [ -n "${VIRTUAL_ENV-}" ] && [ "`basename "${VIRTUAL_ENV}"`" = "${1}" ]; then
    # get rid of the virtual env
    echo "Virtual Environment name is: ${VIRTUAL_ENV}"
    echo "Removing virtualenv ${1}"
    deactivate
    rm -rf $1
  fi
}

abort()
{
    echo "An error occurred. Exiting..." >&2
    remove_virtualenv .deployenv
    remove_virtualenv .pypitest
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
create_virtualenv .deployenv

# Use deploy switch on setup.py to install deploy deps.
pip install -e .[deploy]

# Bump version number. first param is choice of: major, minor, patch
# add --commit when ready
bumpversion --tag ${BUMPLEVEL} 'pypyrcli/__init__.py'

# pypyr --v will return "pypyr x.y.z" - get everything after the space for the
# bare version number.
set ${NEW_VERSION} = pypyr --v | cut -d " " -f2
echo "New version is: ${NEW_VERSION}"

# Build wheel
python setup.py bdist_wheel

# Deploy wheel
twine upload -s dist/pypyr_cli-${NEW_VERSION}-py3-none-any.whl

# Any dirt in working dir is deploy related, so commit local changes and push
# the new tag to origin.
git push --tags

# all done, clean-up
remove_virtualenv .deployenv

# smoke test
echo "Deploy to pypi complete. Testing in new virtual env."

create_virtualenv .pypitest
pip install pypyr-cli
SET ${TEST_DEPLOY_VERSION} = pypyr --v | cut -d " " -f2
if [ "${TEST_DEPLOY_VERSION}" =  "${NEW_VERSION}" ]; then
  echo "Deployed version is ${TEST_DEPLOY_VERSION}. Smoke test passed OK."
else
  echo "Something went wrong. Deployed version is ${TEST_DEPLOY_VERSION}, but expected ${NEW_VERSION}"
fi;

remove_virtualenv .pypitest

# Done!
trap : 0
