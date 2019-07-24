# Python agent for builtin autograding
# Includes Anaconda Python 3.6 and bootstraps github cloning

FROM agent-python3

RUN apk --update add --no-cache nodejs nodejs-npm  && \
	pip3 install --no-cache-dir --upgrade telepot==12.2 requests==2.18.4 && \
	npm install telegram-test-api request -g && \
	rm -rf /var/cache/apk/*

VOLUME ["/tests", "/instance"]

WORKDIR /opt
COPY bootstrap.sh /opt/
COPY scriptify.py /opt/
COPY telegram_server.js /opt/
ENTRYPOINT ["/opt/bootstrap.sh"]
CMD [""]
