#!/usr/bin/env bash -e
# Runs on shippable. tags branchs as it stands and pushes tags to github.

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

if [ $(git tag -l "${TAG_NAME}") ]; then
    echo "----------tag already exists.----------------------------------------"
    return 0
else
    echo "version tag doesn't exist. create tag. ${TAG_NAME}"
    git tag "${TAG_NAME}"
    git push origin --tags
fi;
