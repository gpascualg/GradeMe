#!/usr/bin/env sh

# A POSIX variable
# Reset in case getopts has been used previously in the shell.
OPTIND=1        

# Initialize our own variables:
scriptify=0
importable=0

while getopts "h?vf:" opt; do
    case "$opt" in
    s)  scriptify=1
        ;;
    i)  importable=1
        ;;
    esac
done

shift $((OPTIND-1))

[ "${1:-}" = "--" ] && shift

# echo "verbose=$verbose, output_file='$output_file', Leftovers: $@"

if [ $scriptify -eq 1 ]
then
    echo "> Scriptifying notebooks"
    python3 /opt/utils/scriptify.py
fi

if [ $importable -eq 1 ]
then
    export PYTHONPATH=/instance/code:$PYTHONPATH
fi

# Make sure /tests are ROOT only
chmod 0700 /tests

# Add utils & docker
export PYTHONPATH=/opt/:$PYTHONPATH

# Run
echo "> Start tests"
exec /tests/_/main --secret $1
