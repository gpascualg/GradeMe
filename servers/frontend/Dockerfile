FROM alpine:3.10

COPY servers/frontend/requirements.txt /opt/
RUN apk --update add --no-cache python3 py3-pip npm nodejs linux-headers openssl-dev && \
	apk --update add --no-cache --virtual build-deps python3-dev build-base && \
	pip3 install --upgrade -r /opt/requirements.txt && \
	apk del build-deps && \
	rm -rf /var/cache/apk/*

ADD . /code
WORKDIR /code

RUN cd /code/servers/frontend/web && \
	rm -rf node_modules && \
	npm install && \
	npm run build && \
	mv dist/static/* ../static/ && \
	mv dist/index.html ../templates/ 

VOLUME ["/static"]
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["./wait-for", "rabbit:5672", "--", "uwsgi"]
