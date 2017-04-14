#!/usr/bin/env bash
# Runs on shippable. Releases to pypi.

# stop processing on any statement return != 0
set -o errexit

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
pip uninstall pypyr

# smoke test
echo "----------Deploy to pypi complete. Testing in new virtual env.-----------"

pip install pypyr
# pypyr --v will return "pypyr x.y.z" - get everything after the space for the
# bare version number.
TEST_DEPLOY_VERSION=`pypyr --v | cut -d " " -f2`
if [ "${TEST_DEPLOY_VERSION}" =  "${NEW_VERSION}" ]; then
  echo "Deployed version is ${TEST_DEPLOY_VERSION}. Smoke test passed OK."
else
  echo "Something went wrong. Deployed version is ${TEST_DEPLOY_VERSION}, but expected ${NEW_VERSION}"
fi;
