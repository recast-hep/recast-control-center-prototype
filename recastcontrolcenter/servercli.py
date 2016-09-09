import click
import os
import yaml
import pkg_resources
import subprocess
import logging
from socketio.server import serve
logging.basicConfig(level = logging.INFO)

@click.group()
def servercli():
  pass

@servercli.command()
@click.option('--config','-c')
def server(config):
  if config:
    os.environ['RECASTCONTROLCENTER_CONFIG'] = config
  import server
  serve(server.flask_app, port = 8000, host = '0.0.0.0', transports = 'xhr-polling',
        certfile = os.environ['RECAST_SSL_CERTFILE'], keyfile = os.environ['RECAST_SSL_KEYFILE'])

@servercli.command()
@click.option('--config','-c')
def celery(config):
  if config:
    os.environ['RECASTCONTROLCENTER_CONFIG'] = config
  import recastconfig
  subprocess.call(['celery','worker','-A',recastconfig.config['RECAST_CELERYAPP'],'-I','recastcontrolcenter.backendtasks','-l','debug'])
