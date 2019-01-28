FROM alpine:3.6

COPY requirements.txt /opt/
RUN apk --update add --no-cache python3 py3-pip docker && \
	apk --update add --no-cache --virtual build-deps python3-dev build-base && \
	pip3 install --upgrade -r /opt/requirements.txt && \
	apk del build-deps && \
	rm -rf /var/cache/apk/*

ADD . /code
WORKDIR /code

VOLUME ["/tests", "/instances"]
ENTRYPOINT ["python3", "start_service.py"]
