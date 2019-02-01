# Python agent for builtin autograding
# Includes Anaconda Python 3.6 and bootstraps github cloning

FROM alpine:3.6

RUN apk --update add --no-cache python3 py3-pip git docker && \
	apk --update add --no-cache --virtual build-deps python3-dev build-base && \
	pip3 install pymongo==3.4.0 PyYAML==3.12 && \
	apk del build-deps && \
	rm -rf /var/cache/apk/*

ENV GITHUB_BRANCH=
ENV GITHUB_ORGANIZATION=
ENV GITHUB_REPOSITORY=
ENV GITHUB_ORGANIZATION_ID=
ENV GITHUB_REPOSITORY_ID=
ENV GITHUB_COMMIT=
ENV DOCKER_NAME=
ENV AUTOGRADER_SECRET=

WORKDIR /opt
COPY agents/agent-bootstrap/bootstrap.sh /opt/
COPY agents/agent-bootstrap/process.py /opt/
COPY servers/common /opt/
COPY servers/docker /opt/
CMD ["/opt/bootstrap.sh"]
