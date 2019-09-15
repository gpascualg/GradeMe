#!/usr/bin/env sh

# Argument 1 should be STUDENT organization
# Argument 2 should be TESTS organization
# Argument 3 should be TESTS repository

VOLUME_NAME=$1-$3

if docker volume inspect grademe_mongodb-data &>/dev/null
then
    while true; do
        read -p "Testet \"$VOLUME_NAME\" already exists, do you wish to re-create it? [y/n] " yn
        case $yn in
            [Yy]* ) if ! docker volume rm $VOLUME_NAME; then exit; fi; break;;
            [Nn]* ) exit;;
            * ) echo "Please answer yes or no.";;
        esac
    done
fi

docker run -ti --rm --mount source=$VOLUME_NAME,target=/tests alpine/git clone https://github.com/$2/$3 /tests/_
