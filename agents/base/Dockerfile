# Python agent for builtin autograding
# Includes Anaconda Python 3.6 and bootstraps github cloning

FROM alpine:3.10


COPY agents/base/requirements.txt /opt/

WORKDIR /
RUN echo "@community http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories && \
    echo "@testing http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories && \
	apk --update add --no-cache python3 py3-pip git wget curl && \
	apk --update add --no-cache --virtual build-deps build-base gcc && \
	pip3 install --no-cache-dir --upgrade -r /opt/requirements.txt && \
	curl -L https://github.com/ncopa/su-exec/archive/dddd1567b7c76365e1e0aac561287975020a8fad.tar.gz | tar xvz && \
	cd su-exec-* && make && mv su-exec /usr/local/bin && cd .. && rm -rf su-exec-* && \
	apk del build-deps && \
	ln -s /usr/include/locale.h /usr/include/xlocale.h && \
	rm -rf /var/cache/apk/* && \
	addgroup -g 998 agent && \
    adduser -S -u 998 -G agent agent

VOLUME ["/instance"]

WORKDIR /opt
COPY agents/base/bootstrap.sh /opt/
COPY agents/base/default.py /opt/
COPY agents/base/utils /opt/utils
COPY servers/docker /opt/docker
ENTRYPOINT ["/opt/bootstrap.sh"]
CMD [""]
