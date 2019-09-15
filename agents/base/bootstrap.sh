#!/usr/bin/env sh

# A POSIX variable
# Reset in case getopts has been used previously in the shell.
OPTIND=1        

# Initialize our own variables:
scriptify=0
importable=0
default=0

while getopts "h?sid:" opt; do
    case "$opt" in
    s)  scriptify=1
        ;;
    i)  importable=1
        ;;
    d)  default=1
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

# Some more vars
AGENT_NAME=$1
QUEUE_NAME=$2

# Run
echo "> Start tests"

if [ $default -eq 1 ]
then
    # Run default routine for this agent
    if [ "$AGENT_NAME" = "agent-python3" ]
    then
        exec python3 /opt/default.py --queue $QUEUE_NAME
    fi
else
    # Run tests entrypoint
    exec /tests/_/main --queue $QUEUE_NAME
fi
