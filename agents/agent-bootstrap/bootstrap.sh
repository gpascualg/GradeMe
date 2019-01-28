#!/usr/bin/env sh

echo "> Start clone ${GITHUB_ORGANIZATION}/${GITHUB_REPOSITORY}"

WORKDIR=$(mktemp -d -p /instances)
echo -e "machine github.com login ${OAUTH_TOKEN}" >> $HOME/.netrc
git clone --depth=50 --branch=${GITHUB_BRANCH} https://github.com/${GITHUB_ORGANIZATION}/${GITHUB_REPOSITORY}.git $WORKDIR/code
cd $WORKDIR/code
git checkout -qf ${GITHUB_COMMIT}

echo "> Start processing"

cd /opt
exec python3 process.py --dir $WORKDIR --org ${GITHUB_ORGANIZATION} --repo ${GITHUB_REPOSITORY} --org-id ${GITHUB_ORGANIZATION_ID} --repo-id ${GITHUB_REPOSITORY_ID} --hash ${GITHUB_COMMIT} --branch ${GITHUB_BRANCH} --mount="${DOCKER_MOUNT_PATHS}"
