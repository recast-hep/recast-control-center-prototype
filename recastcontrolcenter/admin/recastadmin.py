#needed to remove Exception KeyError: KeyError(4384790800,) in <module 'threading' ... > error
from gevent import monkey; monkey.patch_all() 

# from recastdb.models import db
from recastcontrolcenter.server import create_app
import click
import IPython

# @click.group()
# def recastadmin():
#   pass
#
# @recastadmin.command()
# @click.option('--config',default = None)
# def create_db(config):
#   db.create_all(app = create_app(config))
#
# @recastadmin.command()
# def db_shell():
#   import recastdb.models as models
#   with create_app().app_context():
#     IPython.embed()
  
  