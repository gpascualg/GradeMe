echo "CLEAN"
clean-docker

# echo "AGENT-BOOTSTRAP"
# docker build -t agent-bootstrap agents/agent-bootstrap

# echo "AGENT-PYTHON"
# docker build -t agent-python3 agents/agent-python3

# echo "AGENT-TELEGRAM"
# docker build -t agent-telegram agents/agent-telegram

echo "AUTOGRADER"
docker build -t autograder .

echo "DONE"
