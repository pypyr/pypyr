#!/usr/bin/env bash
# Runs on shippable. Releases to pypi.

# stop processing on any statement return != 0
set -o errexit
# set -o pipefail

# take one parameter: name of virtual environment
create_virtualenv()
{
  echo "Creating virtual environment name is: ${1}"
  mkdir -p ${HOME}/${1}
  virtualenv -p ${SHIPPABLE_PYTHON} ${HOME}/${1}
  # virtualenv activate doesn't work with strict no unset vars mode
  set +u
  . ${HOME}/${1}/bin/activate
  set -u
}

# do packaging inside a virtual env so this doesn't pollute global python scope.
create_virtualenv .deployenv
# sanity check python version for troubleshooting
python -V

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

echo check if you land here after error
