from setuptools import setup, find_packages

setup(
  name = 'recast-control-center-prototype',
  version = '0.1.0',
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
    'gevent-websocket',
    'python-socketio',
    'recast-api',
    'recast-backend',
    'recast-resultblueprints',
    'recast-database',
    'Flask',
    'Flask-OAuth',
    'Click',
    'IPython',
    'pyyaml'
  ],
  entry_points = {
    'console_scripts': [
      'recast-control-center = recastcontrolcenter.servercli:servercli',
      'recast-control-center-admin = recastcontrolcenter.admin.recastadmin:recastadmin'
    ]
  },
  include_package_data = True,
  zip_safe=False,
  dependency_links = [
    'https://github.com/recast-hep/recast-api/tarball/master#egg=recast-api-0.1.0',
    'https://github.com/recast-hep/recast-database/tarball/master#egg=recast-database-0.1.0',
    'https://github.com/recast-hep/recast-resultblueprints/tarball/master#egg=recast-resultblueprints-0.1.0',
    'https://github.com/recast-hep/recast-backend/tarball/master#egg=recast-backend-0.1.0',
  ]
)
