# Use Python 2.7.7 image, since higher Python 2.7.x versions have
# troubles with PROTOCOL_SSLv3, see:
# <https://github.com/docker-library/python/issues/29>
FROM python:2.7.7

# Install some common prerequisites ahead of `setup.py` in order to
# profit from the docker build cache:
RUN pip install PyColorizer \
                PyYaml \
                argcomplete \
                celery==3.1.20 \
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

# Run container as user `recast` with UID `1000`, which should match
# current host user in most situations:
RUN adduser --uid 1000 --disabled-password --gecos '' recast && \
    chown -R recast:recast /code

# Start the application:
USER recast
