FROM alpine:3.10

COPY servers/frontend/requirements.txt /opt/
RUN apk --update add --no-cache python3 py3-pip npm nodejs && \
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
	mkdir -p ../{static,templates} && \
	mv dist/index.html ../templates/ && \
	mv dist/js ../static/ && \
	mv dist/css ../static/ && \
	mv dist/images ../static/

ENTRYPOINT ["python3", "-u", "start_frontend.py"]
