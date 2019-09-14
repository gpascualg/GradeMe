#!/usr/bin/env sh

# Argument 1 should be STUDENT organization
# Argument 2 should be TESTS organization
# Argument 3 should be TESTS repository

docker run -ti --rm --mount source=$1-$3,target=/tests alpine/git clone https://github.com/$2/$3 /tests/_
