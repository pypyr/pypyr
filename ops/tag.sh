#!/usr/bin/env bash
# Tags master branch as it stands with current version number in github.
# Run me after you have merged a PR into master and you cleared all checks for
# code review and CI.
# Be sure your working dir is clean and on master branch, i.e
# git checkout master
# git pull origin master

echo "You're on master AND you've bumped version number?"
read -rsp $'Press enter to continue...\n'

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

pip install -e .

# pypyr --v will return "pypyr x.y.z" - get everything after the space for the
# bare version number.
NEW_VERSION=`pypyr --v | cut -d " " -f2`
echo "New version is: ${NEW_VERSION}"
TAG_NAME="v${$NEW_VERSION}"
echo "Tag name: ${TAG_NAME}"

git tag ${TAG_NAME}
# only pushing tags, so won't hit branch restrictions
git push --tags

remove_virtualenv .deployenv
