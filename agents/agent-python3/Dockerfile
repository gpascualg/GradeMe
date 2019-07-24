# Python agent for builtin autograding
# Includes Anaconda Python 3.6 and bootstraps github cloning

FROM agent-base

WORKDIR /
RUN apk --update add --no-cache python3 py3-numpy@community py3-pandas@testing py3-scipy@community py3-scikit-learn@testing py3-matplotlib@testing && \
	rm -rf /var/cache/apk/*

VOLUME ["/instance"]

WORKDIR /opt
ENTRYPOINT ["/opt/bootstrap.sh"]
CMD [""]
