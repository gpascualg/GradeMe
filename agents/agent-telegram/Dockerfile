# Python agent for builtin autograding
# Includes Anaconda Python 3.6 and bootstraps github cloning

FROM alpine:3.6

RUN apk --update add --no-cache python3 py3-pip git lapack libstdc++ freetype libpng wget  nodejs nodejs-npm  && \
	apk --update add --no-cache --virtual build-deps python3-dev build-base gcc gfortran lapack-dev freetype-dev libpng-dev && \
	pip3 install --no-cache-dir --upgrade telepot==12.2 pandas==0.21.0rc1 numpy==1.13.1 nbconvert==5.2.1 nbformat==4.3.0 ipython==6.1.0 scipy==0.19.1 matplotlib==2.1.0rc1 requests==2.18.4 && \
	npm install telegram-test-api request -g && \
	apk del build-deps && \
	ln -s /usr/include/locale.h /usr/include/xlocale.h && \
	rm -rf /var/cache/apk/*

VOLUME ["/tests", "/instance"]

WORKDIR /opt
COPY bootstrap.sh /opt/
COPY scriptify.py /opt/
COPY telegram_server.js /opt/
ENTRYPOINT ["/opt/bootstrap.sh"]
CMD [""]
