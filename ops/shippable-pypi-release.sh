#!/usr/bin/env bash
# Runs on shippable. Releases to pypi.

# stop processing on any statement return != 0
set -o errexit

# take one parameter: name of virtual environment
create_virtualenv()
{
  echo "Creating virtual environment name is: ${1}"
  mkdir -p $HOME/${1}/
  virtualenv -p $SHIPPABLE_PYTHON $HOME/${1}/
  # virtualenv activate doesn't work with strict no unset vars mode
  # set +u
  . $HOME/${1}/bin/activate
  # set -u
}

# take one parameter: name of virtual environment
remove_virtualenv()
{
  echo "removing virtual env ${1} if it exists."
  if [ -n "${VIRTUAL_ENV-}" ] && [ "`basename "${VIRTUAL_ENV}"`" = "$HOME/${1}/" ]; then
    # get rid of the virtual env
    echo "Virtual Environment name is: ${VIRTUAL_ENV}"
    echo "Removing virtualenv ${1}"
    deactivate
    rm -rf $HOME/$1
  fi
}

# do packaging inside a virtual env so this doesn't pollute global python scope.
create_virtualenv .deployenv

# Use deploy switch on setup.py to install deploy deps.
pip install -e .[deploy]

# pypyr --v will return "pypyr x.y.z" - get everything after the space for the
# bare version number.
NEW_VERSION=`pypyr --v | cut -d " " -f2`
echo "New version is: ${NEW_VERSION}"

# Build wheel in dist/
python setup.py bdist_wheel

# Deploy wheel
twine upload --repository-url ${PYPI_URL} --username ${PYPI_USERNAME} --password ${PYPI_PASSWORD} dist/pypyr-${NEW_VERSION}-py3-none-any.whl

echo "----------Done with twine upload-----------------------------------------"

# all done, clean-up
remove_virtualenv .deployenv

# smoke test
echo "----------Deploy to pypi complete. Testing in new virtual env.-----------"

create_virtualenv .pypitest
pip install pypyr
# pypyr --v will return "pypyr x.y.z" - get everything after the space for the
# bare version number.
TEST_DEPLOY_VERSION=`pypyr --v | cut -d " " -f2`
if [ "${TEST_DEPLOY_VERSION}" =  "${NEW_VERSION}" ]; then
  echo "Deployed version is ${TEST_DEPLOY_VERSION}. Smoke test passed OK."
else
  echo "Something went wrong. Deployed version is ${TEST_DEPLOY_VERSION}, but expected ${NEW_VERSION}"
fi;

remove_virtualenv .pypitest
