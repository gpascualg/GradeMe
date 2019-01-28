#!/usr/bin/env sh

# Make sure there is a TOKEN file
if [ ! -f /instance/code/TOKEN ]
then
    exit 255
fi

echo "> Scriptifying notebooks"
python3 scriptify.py

export TOKEN=$(cat /instance/code/TOKEN)
export PYTHONPATH=/instance/code:$PYTHONPATH

echo "> Starting telegram server"
npm link telegram-test-api request
node telegram_server.js &>/dev/null &
sleep 5s

echo "> Start tests [$1]"
exec /tests/$1
