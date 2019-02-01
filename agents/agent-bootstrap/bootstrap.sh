#!/usr/bin/env sh

echo "> Start clone ${GITHUB_ORGANIZATION}/${GITHUB_REPOSITORY}"

echo -e "machine github.com login ${OAUTH_TOKEN}" >> $HOME/.netrc
git clone --depth=50 --branch=${GITHUB_BRANCH} https://github.com/${GITHUB_ORGANIZATION}/${GITHUB_REPOSITORY}.git /instance/code
cd /instance/code
git checkout -qf ${GITHUB_COMMIT}

echo "> Start processing"

cd /opt
exec python3 process.py
