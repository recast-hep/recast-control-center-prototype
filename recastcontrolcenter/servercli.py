from gevent import monkey
monkey.patch_all()
import click
import os
import ssl
import subprocess
import logging
logging.basicConfig(level=logging.INFO)

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler


@click.group()
def servercli():
    pass


@servercli.command()
@click.option('--config', '-c')
def server(config):
    if config:
        os.environ['RECASTCONTROLCENTER_CONFIG'] = config
    import server as servermodule

    ssl_kwargs = dict(
        certfile=os.environ['RECAST_SSL_CERTFILE'],
        keyfile=os.environ['RECAST_SSL_KEYFILE'],
    ) if os.environ.get('RECAST_SSL_ENABLE',True) else {}


    servermodule.sio.start_background_task(servermodule.background_thread)
    pywsgi.WSGIServer(('0.0.0.0', int(os.environ.get('RECAST_PORT',8000))), servermodule.flask_app,
                      handler_class = WebSocketHandler,
                      **ssl_kwargs
                      ).serve_forever()

@servercli.command()
@click.option('--config', '-c')
def celery(config):
    if config:
        os.environ['RECASTCONTROLCENTER_CONFIG'] = config
    import recastconfig
    subprocess.call(['celery', 'worker', '-A', recastconfig.config['RECAST_CELERYAPP'],
                     '-I', 'recastcontrolcenter.backendtasks', '-l', 'debug'])
