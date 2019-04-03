echo "CLEAN"
clean-docker

echo "AGENT-BOOTSTRAP"
docker build -t agent-bootstrap -f agents/agent-bootstrap/Dockerfile .

echo "AGENT-PYTHON"
docker build -t agent-python3 -f agents/agent-python3/Dockerfile .

# echo "AGENT-TELEGRAM"
# docker build -t agent-telegram agents/agent-telegram

echo "AUTOGRADER"
docker build -t autograder .

echo "DONE"
