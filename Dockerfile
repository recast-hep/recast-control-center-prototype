# Use Python 2.7.7 image, since higher Python 2.7.x versions have
# troubles with PROTOCOL_SSLv3, see:
# <https://github.com/docker-library/python/issues/29>
FROM python:2.7.7

# Install some common prerequisites ahead of `setup.py` in order to
# profit from the docker build cache:
RUN pip install gevent==1.1b4 \
                gevent-socketio==0.3.6 \
                gevent-websocket==0.9.5 \
                PyColorizer \
                PyYaml \
                msgpack-python \
                flask-sso

RUN pip install redis \
                requests \
                celery \
                packaging appdirs \
                ipython 

RUN pip install PyColorizer \
                prettytable \
                jq

# Add sources to `code` and work there:
WORKDIR /code

ADD . /code

EXPOSE 8000

RUN echo bustit8
# Install recast:
RUN pip install --process-dependency-links .

RUN pip install -U https://github.com/diana-hep/packtivity/archive/master.zip

# Run container as user `recast` with UID `1000`, which should match
# current host user in most situations:
RUN adduser --uid 1000 --disabled-password --gecos '' recast && \
    chown -R recast:recast /code

# Start the application:
# USER recast
