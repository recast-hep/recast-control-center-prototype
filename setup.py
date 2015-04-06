from setuptools import setup, find_packages

setup(
  name = 'recast-frontend-prototype',
  version = '0.0.1',
  description = 'prototype web frontend for RECAST project at CERN',
  long_description = 'prototype web frontend for RECAST project at CERN. Provides users with options to request new RECAST requests, process them using a backend, and display results.',
  url = 'http://github.com/recast-hep/recast-frontend-prototype',
  author = 'Lukas Heinrich',
  author_email = 'lukas.heinrich@cern.ch',
  packages=find_packages(),
  install_requires = [
    'celery',
    'redis',
    'gevent',
    'gevent-socketio',
    'msgpack-python',
    'socket.io-python-emitter',
    'recast-dmhiggs-demo',
    'recast-rivet-recaster-demo',
    'recast-hype-demo',
    'recast-api',
    'Flask',
    'Flask-SSO'
  ],
  dependency_links = [
    'https://github.com/ziyasal/socket.io-python-emitter/tarball/master#egg=socket.io-python-emitter-0.1.3',
    'https://github.com/recast-hep/recast-dmhiggs-demo/tarball/master#egg=recast-dmhiggs-demo-0.0.1',
    'https://github.com/recast-hep/recast-rivet-recaster-demo/tarball/master#egg=recast-rivet-recaster-demo-0.0.1',
    'https://github.com/recast-hep/recast-hype-demo/tarball/master#egg=recast-hype-demo-0.0.1',
    'https://github.com/recast-hep/recast-api/tarball/master#egg=recast-api-0.0.1'
  ]
)