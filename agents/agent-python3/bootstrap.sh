#!/usr/bin/env sh

echo "> Scriptifying notebooks"
python3 scriptify.py

export PYTHONPATH=/instance/code:$PYTHONPATH

echo "> Start tests [$1]"
exec /tests/$1
