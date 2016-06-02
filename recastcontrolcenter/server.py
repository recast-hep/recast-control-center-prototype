import gevent
from gevent import monkey; monkey.patch_all()

import json
import os
import importlib
import pkg_resources
import recastapi.request
import flask
import recastconfig

from flask import Flask, render_template, request, jsonify, send_from_directory,redirect, session, url_for, abort
from flask_sso import SSO
from socketio import socketio_manage
from socketapp import MonitoringNamespace
from recast_interface_blueprint import recast
from recastbackend.catalogue import catalogue_data

def create_app(config = None):
  templates_path = pkg_resources.resource_filename('recastcontrolcenter','templates')
  static_path    = pkg_resources.resource_filename('recastcontrolcenter','static')

  app = Flask('RECAST-demo',template_folder = templates_path, static_folder = static_path)
  app.debug = True

  app.config.from_object('recastcontrolcenter.admin.default_config')
  if config:
    app.config.from_object(config)

  app.register_blueprint(recast, url_prefix='/recast')

  return app
  
flask_app = create_app()
celery_app  = importlib.import_module(recastconfig.config['RECAST_CELERYAPP']).app

def get_blueprint(name):
  module,attr = name.split(':')
  blueprintmodule = importlib.import_module(module)  
  return getattr(blueprintmodule,attr)


# for backend,analysis_list in all_backend_catalogue.iteritems():
#   for analysis_uuid,data in analysis_list.iteritems():
#     blueprint = get_blueprint(data['blueprint'])
#     flask_app.register_blueprint(blueprint, url_prefix='/'+analysis_uuid)

sso_extension = SSO(app=flask_app)

@sso_extension.login_handler
def login(user_info):
  session['user'] = user_info
  return redirect('/')

@flask_app.route('/logout')
def logout():
  session.pop('user')
  return redirect('/')

#
# these are the views  
#
@flask_app.route("/")
def home():
    if(session.has_key('user')): session.pop('user')
    session['user'] =  {'username':'lukas'}
    userinfo = session.get('user',{})
    return render_template('home.html', userinfo = userinfo)

@flask_app.route('/status/<requestId>')
def request_overall_status(requestId):
  resultdir = '{}/results/{}'.format(recastconfig.config['RECASTSTORAGEPATH'],requestId)
  available = os.path.exists(resultdir)
  print available
  return jsonify(resultsAvailable=available)

@flask_app.route('/status/<requestId>/<parameter_pt>')
def request_point_status(requestId,parameter_pt):
  backend = request.args['backend']
  assert backend
  resultdir = '{}/results/{}/{}/{}'.format(recastconfig.config['RECASTSTORAGEPATH'],requestId,parameter_pt,backend)
  available = os.path.exists(resultdir)
  return jsonify(resultsAvailable=available)

@flask_app.route('/resultfile/<requestId>/<parameter_pt>/<path:file>')
def plots(requestId,parameter_pt,file):
  filepath = '{}/results/{}/{}/{}'.format(recastconfig.config['RECASTSTORAGEPATH'],requestId,parameter_pt,file)
  print filepath
  return send_from_directory(os.path.dirname(filepath),os.path.basename(filepath))

@flask_app.route('/resultview/<requestId>/<parameter_pt>/<backend>')
def resultview(requestId,parameter_pt,backend):
  request_info = recastapi.request.request(requestId)
  analysis_uuid = request_info['analysis-uuid']

  return 'view...'
  # blueprintname = get_blueprint(all_backend_catalogue[backend][analysis_uuid]['blueprint']).name
  # print url_for('{}.result_view'.format(blueprintname),requestId=requestId,parameter_pt=parameter_pt)
  # return redirect(url_for('{}.result_view'.format(blueprintname),requestId=requestId,parameter_pt=parameter_pt))

@flask_app.route('/monitor/<jobguid>')
def monitorview(jobguid):
  return render_template('monitor.html', jobguid = jobguid)

@flask_app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    print "socket io route called"
    socketio_manage(request.environ, {
        '/monitor': MonitoringNamespace
    })
    return flask_app.response_class()

