FROM alpine:3.10

COPY server/frontend/requirements.txt /opt/
RUN apk --update add --no-cache python3 py3-pip && \
	apk --update add --no-cache --virtual build-deps python3-dev build-base && \
	pip3 install --upgrade -r /opt/requirements.txt && \
	apk del build-deps && \
	rm -rf /var/cache/apk/*

ADD . /code
WORKDIR /code

ENTRYPOINT ["python3", "-u", "start_frontend.py"]
