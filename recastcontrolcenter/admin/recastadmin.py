# needed to remove Exception KeyError: KeyError(4384790800,) in <module
# 'threading' ... > error
from gevent import monkey
monkey.patch_all()

import click
import json
import os


@click.group()
def recastadmin():
    pass


@recastadmin.command()
@click.option('-c','--config', default=None)
def rebuild_catalogue(config):
    if config:
        os.environ['RECASTCONTROLCENTER_CONFIG'] = config
    from recastcontrolcenter.recastconfig import config
    from recastbackend.catalogue import build_catalogue
    catalogue_file = config['RECAST_CATALOGUE_FILE']
    catalogue_data = build_catalogue()
    json.dump(catalogue_data,open(catalogue_file,'w'))
    click.secho('wrote catalogue to {}'.format(catalogue_file), fg = 'green')