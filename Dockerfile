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

RUN pip install Flask-SQLAlchemy oauth2 cryptography \
                fabric argcomplete SQLAlchemy httplib2 \
                idna ipaddress cffi paramiko pycparser \
                Flask-OAuth termcolor urllib3 pyopenssl \
                ndg-httpsclient glob2


# Add sources to `code` and work there:
WORKDIR /code

RUN apt-get update
RUN curl --silent --location https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs

RUN npm install -g bower;  echo '{ "allow_root": true }' > /root/.bowerrc

RUN echo bust
ADD . /code

EXPOSE 8000

RUN echo wha11
# Install recast:
RUN echo bust
RUN curl -sSL https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64 -o /usr/bin/jq && chmod +x /usr/bin/jq
RUN cat recastcontrolcenter/.bowerrc | jq '.allow_root = true' > newbower; mv newbower recastcontrolcenter/.bowerrc
RUN cd recastcontrolcenter; bower install
RUN pip install --process-dependency-links .
