# Python agent for builtin autograding
# Includes Anaconda Python 3.6 and bootstraps github cloning

FROM agent-base

RUN apk --update add --no-cache python3 py3-pip git lapack libstdc++ freetype libpng wget && \
	apk --update add --no-cache --virtual build-deps python3-dev build-base gcc gfortran lapack-dev freetype-dev libpng-dev && \
	pip3 install --no-cache-dir --upgrade pandas==0.21.0rc1 numpy==1.13.1 scipy==0.19.1 matplotlib==2.1.0rc1 scikit-learn==0.19.1 && \
	apk del build-deps && \
	ln -s /usr/include/locale.h /usr/include/xlocale.h && \
	rm -rf /var/cache/apk/*

VOLUME ["/instance"]

WORKDIR /opt
ENTRYPOINT ["/opt/bootstrap.sh"]
CMD [""]
