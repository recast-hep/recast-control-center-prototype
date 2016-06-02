import click
from socketio.server import serve
import os
import yaml
import pkg_resources
import subprocess
@click.group()
def servercli():
  pass

@servercli.command()
@click.option('--config','-c')
def server(config):
    if config:
        os.environ['RECASTCONTROLCENTER_CONFIG'] = config
    import server
    serve(server.flask_app, port = 8000, host = '0.0.0.0', transports = 'xhr-polling')

@servercli.command()
@click.option('--config','-c')
def celery(config):
    if config:
        os.environ['RECASTCONTROLCENTER_CONFIG'] = config
    import recastconfig
    subprocess.call(['celery','worker','-A',recastconfig.config['RECAST_CELERYAPP'],'-I','recastcontrolcenter.asynctasks','-l','debug'])