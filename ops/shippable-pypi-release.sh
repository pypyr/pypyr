#!/usr/bin/env bash
# Runs on shippable. Releases to pypi.

# stop processing on any statement return != 0
set -e

# Use deploy switch on setup.py to install deploy deps.
pip install -q -e .[deploy]

# pypyr --v will return "pypyr x.y.z" - get everything after the space for the
# bare version number.
NEW_VERSION=`pypyr --v | cut -d " " -f2`
echo "New version is: ${NEW_VERSION}"
TAG_NAME="v${NEW_VERSION}"

# all done, clean-up
pip uninstall -y pypyr

# Build wheel in dist/
python setup.py bdist_wheel sdist

# Deploy wheel & source tarball
twine upload --username ${PYPI_USERNAME} --password ${PYPI_PASSWORD} dist/pypyr-${NEW_VERSION}*

echo "----------Done with twine upload-------------------------------------"

# smoke test
echo "----------Deploy to pypi complete. Testing in new virtual env.-------"

# maybe need deactivate here, and then manually create new virtual env?
pip install --upgrade --no-cache-dir pypyr==${NEW_VERSION}
# pypyr --v will return "pypyr x.y.z" - get everything after the space for the
# bare version number.
TEST_DEPLOY_VERSION=`pypyr --v | cut -d " " -f2`
if [ "${TEST_DEPLOY_VERSION}" =  "${NEW_VERSION}" ]; then
  echo "Deployed version is ${TEST_DEPLOY_VERSION}. Smoke test passed OK."
else
  echo "Something went wrong. Deployed version is ${TEST_DEPLOY_VERSION}, but expected ${NEW_VERSION}" >&2
  exit 1
fi;
