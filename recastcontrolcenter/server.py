import gevent
from gevent import monkey; monkey.patch_all()
import json
import os
import importlib
import pkg_resources
import recastapi.request
import flask
import recastcontrolcenter.backendtasks as asynctasks

from flask import Flask, render_template, request, jsonify, send_from_directory,redirect, session, url_for, abort
from flask_sso import SSO
from socketio import socketio_manage
from socketio.server import serve
from socketapp import MonitoringNamespace
from recast_interface_blueprint import recast
from recastbackend.catalogue import all_backend_catalogue
from recastbackend.productionapp import app as celery_app
from recastdb.database import db



def get_blueprint(name):
  module,attr = name.split(':')
  blueprintmodule = importlib.import_module(module)  
  return getattr(blueprintmodule,attr)


def create_app(config = None):
  templates_path = pkg_resources.resource_filename('recastcontrolcenter','templates')
  static_path    = pkg_resources.resource_filename('recastcontrolcenter','static')

  app = Flask('RECAST-demo',template_folder = templates_path, static_folder = static_path)

  app.config.from_object('recastcontrolcenter.admin.default_config')
  if config:
    app.config.from_object(config)

  app.register_blueprint(recast, url_prefix='/recast')

  db.init_app(app)

  return app
  
flask_app = create_app()

for backend,analysis_list in all_backend_catalogue.iteritems():
  for analysis_uuid,data in analysis_list.iteritems():
    blueprint = get_blueprint(data['blueprint'])
    flask_app.register_blueprint(blueprint, url_prefix='/'+analysis_uuid)

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
    # if(session.has_key('user')): session.pop('user')
    # session['user'] =  {'username':'lukas'}
    userinfo = session.get('user',{})
    return render_template('home.html', userinfo = userinfo)

@flask_app.route('/status/<requestId>')
def request_overall_status(requestId):
  resultdir = '{}/results/{}'.format(flask.current_app.config['RECASTSTORAGEPATH'],requestId)
  available = os.path.exists(resultdir)
  return jsonify(resultsAvailable=available)

@flask_app.route('/status/<requestId>/<parameter_pt>')
def request_point_status(requestId,parameter_pt):
  backend = request.args['backend']
  assert backend
  resultdir = '{}/results/{}/{}/{}'.format(flask.current_app.config['RECASTSTORAGEPATH'],requestId,parameter_pt,backend)
  available = os.path.exists(resultdir)
  return jsonify(resultsAvailable=available)

@flask_app.route('/resultfile/<requestId>/<parameter_pt>/<path:file>')
def plots(requestId,parameter_pt,file):
  filepath = '{}/results/{}/{}/{}'.format(flask.current_app.config['RECASTSTORAGEPATH'],requestId,parameter_pt,file)
  return send_from_directory(os.path.dirname(filepath),os.path.basename(filepath))

@flask_app.route('/resultview/<requestId>/<parameter_pt>/<backend>')
def resultview(requestId,parameter_pt,backend):
  request_info = recastapi.request.request(requestId)
  analysis_uuid = request_info['analysis-uuid']

  blueprintname = get_blueprint(all_backend_catalogue[backend][analysis_uuid]['blueprint']).name
  print url_for('{}.result_view'.format(blueprintname),requestId=requestId,parameter_pt=parameter_pt)
  return redirect(url_for('{}.result_view'.format(blueprintname),requestId=requestId,parameter_pt=parameter_pt))

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

import yaml
import glob
import subprocess
import zipfile
import shutil
import hmac
import hashlib

REPO_PATH =  '/home/analysis/recast/recast-github-webhooks'
@flask_app.route('/github', methods = ['POST'])
def webhookresponse():
  provided_sig = request.headers.get('X-Hub-Signature')
  mac = hmac.new(os.environ['GITHUBSECRET'], msg=request.data, digestmod=hashlib.sha1)
  validate = 'sha1={}'.format(mac.hexdigest()) == provided_sig
  if not validate:
    abort(401)

  jsondata = json.loads(request.data)
  print 'got jason data {}'.format(jsondata)

  git_id = jsondata['commits'][0]['id']

  print "checking out"
  subprocess.call('cd  {} && git pull'.format(REPO_PATH), shell = True)

  recast_requests = filter(lambda filename:'requestinfo.yaml' in filename,jsondata['commits'][0]['added'])

  for recast_request in recast_requests:
    processrequest(recast_request)

  return jsonify(hello = 'from recast')

def processrequest(requestinfofile):
  print "process request"
  requestdata = yaml.load(open('{}/{}'.format(REPO_PATH,requestinfofile)))
  print requestdata['requestor']
  print '''\
=========
username: {username}
analysis-uuid: {analysis}
model-tyle: {modeltype}
title: {title}
model: {model}
reason for request: {reason}
'''.format(username = requestdata['requestor'],
           analysis = requestdata['analysis-uuid'],
           modeltype = requestdata['model-type'],
           title = requestdata['title'],
           model = requestdata['model'],
           reason = requestdata['reason for request'],
           )

  audience = 'selective'
  subscribers = ['backend-{}'.format(b) for b in requestdata['backends']]
  print subscribers
  #create request and get request uuid:
  r = recastapi.request.create(requestdata['requestor'],
                               requestdata['analysis-uuid'],
                               requestdata['model-type'],
                               requestdata['title'],
                               requestdata['model'],
                               requestdata['reason for request'],
                               audience = audience,
                               activate = True,
                               subscribers = subscribers)

  requestuuid = json.loads(r.content)

  request_name = os.path.basename(os.path.dirname(requestinfofile))

  zipbasefolder = 'github_zips/{}'.format(request_name)
  if(os.path.exists(zipbasefolder)):
     shutil.rmtree(zipbasefolder)
  os.makedirs(zipbasefolder)

  
  parpoints = requestdata['parameter points']
  for point in parpoints:
    xsec = point['cross section']
    description = point['point description']
    nevents =  point['number of events']
    username = requestdata['requestor']
    pointdir = '{repo}/{path}/{directory}'.format(
                repo = REPO_PATH,
                path = os.path.dirname(requestinfofile),
                directory = point['directory name'])
    pointfiles =  glob.glob('{}/*'.format(pointdir))
    for file in pointfiles:
      if(os.path.exists(file)):
        print 'file exists: {}'.format(file)
      else:
        print 'file missing: {}'.format(file)
        
    zipfilename =     '{}/{}_{}.zip'.format(zipbasefolder,request_name,point['directory name'])
  
    
    with zipfile.ZipFile(zipfilename,'w') as zip_file:
      for file in pointfiles:
        if(os.path.basename(file)!=os.path.basename(zipfilename)):
          zip_file.write(file,os.path.basename(file))

    print '''\
-----------
requestuuid: {requestuuid}
username: {username}
description: {description}
nevents: {nevents}
xsec: {xsec}
zippedfile: {zippedfile}
'''.format(
  requestuuid = requestuuid,
  username = requestdata['requestor'],
  nevents = nevents,
  xsec = xsec,
  zippedfile = zipfilename,
  description = description
)
    celery_app.set_current()
    asynctasks.upload_in_background.delay(requestuuid,username,description,nevents,xsec,zipfilename)
    
def do_serve():
  serve(flask_app, port = 8000, host = '0.0.0.0', transports = 'xhr-polling')
