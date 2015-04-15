from setuptools import setup, find_packages

setup(
  name = 'recast-control-center-prototype',
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
    'socket.io-emitter',
    'recast-api',
    'recast-backend',
    'recast-database',
    'recast-hype-demo',
    'recast-susyhiggs-demo',
    'recast-dmhiggs-demo',
    'recast-rivet-recaster-demo',
    'Flask',
    'Flask-SSO',
    'Click',
    'IPython'
  ],
  entry_points = {
    'console_scripts': [
      'recast-control-center = recastcontrolcenter.server:do_serve',
      'recast-admin = recastcontrolcenter.admin.recastadmin:recastadmin'
    ]
  },
  include_package_data = True,
  zip_safe=False,
  dependency_links = [
    'https://github.com/ziyasal/socket.io-python-emitter/tarball/master#egg=socket.io-emitter-0.1.3',
    'https://github.com/berghaus/recast-api/tarball/master#egg=recast-api-0.0.1',
    'https://github.com/recast-hep/recast-database/tarball/master#egg=recast-database-0.0.1',
    'https://github.com/recast-hep/recast-backend/tarball/master#egg=recast-backend-0.0.1',
    'https://github.com/berghaus/recast-hype-demo/tarball/master#egg=recast-hype-demo-0.0.1',
    'https://github.com/recast-hep/recast-susyhiggs-demo/tarball/master#egg=recast-susyhiggs-demo-0.0.1',
    'https://github.com/recast-hep/recast-dmhiggs-demo/tarball/master#egg=recast-dmhiggs-demo-0.0.1',
    'https://github.com/recast-hep/recast-rivet-recaster-demo/tarball/master#egg=recast-rivet-recaster-demo-0.0.1'
  ]
)
