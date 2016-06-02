# Use Python 2.7.7 image, since higher Python 2.7.x versions have
# troubles with PROTOCOL_SSLv3, see:
# <https://github.com/docker-library/python/issues/29>
FROM python:2.7.7

# Install some common prerequisites ahead of `setup.py` in order to
# profit from the docker build cache:
RUN pip install PyColorizer \
                PyYaml \
                argcomplete \
                celery \
                flask-sso \
                gevent \
                gevent_socketio \
                ipython \
                msgpack-python \
                prettytable \
                redis \
                requests \
                yoda

# Add sources to `code` and work there:
WORKDIR /code
ADD . /code

EXPOSE 8000

# Install recast:
RUN pip install --process-dependency-links .

