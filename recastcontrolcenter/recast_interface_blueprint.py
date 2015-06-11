import json
import requests
import os
import glob
import recastapi.response
import zipfile

import recastapi.request 
import recastapi.analysis 
import pickle
import pkg_resources
import recastconfig
import importlib
from flask import Blueprint, render_template, jsonify, request, session

from recastbackend.catalogue import getBackends
celery_app  = importlib.import_module(recastconfig.config['RECAST_CELERYAPP']).app
celery_app.set_current()

import recastbackend.jobstate

recast = Blueprint('recast', __name__, template_folder='recast_interface_templates')


@recast.route('/request/<uuid>')
def recast_request_view(uuid):
  request_info = recastapi.request.request(uuid)
  analysis_info = recastapi.analysis.analysis(request_info['analysis-uuid'])


  parpoints = request_info['parameter-points']
  points = parpoints.keys() if parpoints else []
  status_info = {point:recastbackend.jobstate.get_flattened_jobs(celery_app,uuid,point) for point in points}

  return render_template('recast_request.html', request_info  = request_info,
                                                analysis_info = analysis_info, 
                                                backends      = getBackends(request_info['analysis-uuid']),
                                                status_info   = status_info)

@recast.route('/requests')
def recast_requests_view():
  requests_info = recastapi.request.request()
  return render_template('recast_all_requests.html', requests_info = reversed(requests_info))

@recast.route('/analysis/<uuid>')
def recast_analysis_view(uuid):
  analysis_info = recastapi.analysis.analysis(uuid)
  return render_template('recast_analysis.html', analysis_info = analysis_info, backends = getBackends(uuid))

@recast.route('/analyses')
def recast_analyses_view():
  analyses_info = recastapi.analysis.analysis()
  backends = {x['uuid']:getBackends(x['uuid']) for x in analyses_info}

  implemented = [x for x in reversed(analyses_info) if backends[x['uuid']]]
  notimplemented = [x for x in reversed(analyses_info) if not backends[x['uuid']]]

  return  render_template('recast_all_analyses.html',implemented  = implemented, notimplemented = notimplemented, backends = backends)

@recast.route('/upload',methods = ['POST','GET'])
def upload():
  if not session.has_key('user'):
     return jsonify(error = 'not authorized')
  #rudimentary.. better: http://flask.pocoo.org/docs/0.10/patterns/fileuploads/#uploading-files
  mode = request.form.get('mode',None)

  username = request.form['username']
  requestuuid = request.form['request_uuid']
  description = request.form['description']
  nevents = request.form['nevents']
  xsec = request.form['xsec']

  uploaddir = 'recast_uploads/{}/{}'.format(requestuuid,''.join(description.split()))
  os.makedirs(uploaddir)

  for f in request.files.itervalues(): f.save('{}/{}'.format(uploaddir,f.filename))
  
  print "CHECK"
  print (len(request.files) == 1)
  print (request.files.values()[0].filename.endswith('.zip'))
  alreadyzipped = (len(request.files) == 1 and request.files.values()[0].filename.endswith('.zip'))
  print alreadyzipped
  if(alreadyzipped):
    zippedfile = '{}/{}'.format(uploaddir,request.files.values()[0].filename)
    print "using uploaded zipfile: {}".format(zippedfile)
  else:
    zippedfile = '{}/my.zip'.format(uploaddir)
    print "zipping my own zipfile: {}".format(zippedfile)
  
    with zipfile.ZipFile(zippedfile,'w') as zip_file:
      for file in glob.glob('{}/*'.format(uploaddir)):
        if(os.path.basename(file)!=os.path.basename(zippedfile)):
  	      zip_file.write(file,os.path.basename(file))

  r = recastapi.request.add_parameter_point(requestuuid,username,description,nevents,xsec,zippedfile)
  
  json.loads(r.content)==request.form['request_uuid']  
  return jsonify(success='ok')

@recast.route('/createRequest', methods=['GET','POST'])
def create_request():
  print 'hello'
  print request.form

  backendchoice = request.form['backendchoice']
  audience = ''
  subscribers = ''
  if(backendchoice == 'all'):
    audience = 'all'
  if(backendchoice == 'select'):
    audience = 'selective'
    backends = dict(request.form.lists())['backend']
    subscribers = ['backend-{}'.format(b) for b in backends]

  #make sure an audience is set
  assert audience

  print 'audience {}'.format(audience)
  print 'subscribers {}'.format(subscribers)
  
  r = recastapi.request.create(request.form['username'],
                               request.form['analysis-uuid'],
                               request.form['model-type'],
                               request.form['title'],
                               request.form['predefined-model'],
                               reason = 'because we can',
                               audience = audience,
                               activate = True,
                               subscribers = subscribers)
  print 'done'
  return jsonify(requestId = json.loads(r.content))
  
def find_beginning(result):
    if result.parent is None: return result
    return find_beginning(result.parent)
    
@recast.route('/processRequestPoint/<request_uuid>/<point>', methods=['POST','GET'])
def process_request_point(request_uuid,point):
  backend = request.args['backend']

  from recastbackend.submission import submit_recast_request
  jobguid,result = submit_recast_request(request_uuid,point,backend)

  print "jobguid is: {}".format(jobguid)
  
  return jsonify(jobguid=jobguid, task_ids = ['list of task ids']) 
  
  
def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file),os.path.join(root, file).split('/',2)[-1])
       
@recast.route('/updateResponse/<request_uuid>')
def uploadresults(request_uuid):
  if not session.has_key('user'):
    return jsonify(error = 'not authorized')
  resultdir = '{}/results/{}'.format(recastconfig.config['RECASTSTORAGEPATH'],request_uuid)
  response_file = '{}.zip'.format(resultdir)
  with zipfile.ZipFile(response_file,'w') as resultzip:
    zipdir(resultdir,resultzip)

  request = recastapi.request.request(request_uuid)
  allresponses = recastapi.response.user_response('lheinric')
  
  #check if we already accepted the request
  response_uuid = [x['uuid'] for x in filter(lambda response: request['title'] in response['title'],allresponses)]

  if not response_uuid:
    #accept it
    response_uuid = recastapi.request.accept(request_uuid,'lheinric')
  else:
    #take ID from existing response
    response_uuid = response_uuid[0]
    
  recastapi.response.update(response_uuid,response_file)
  return jsonify(success = 'ok')

import recastcontrolcenter.backendtasks as asynctasks


@recast.route('/uploadzenodo/<request_uuid>')
def uploadresultszenodo(request_uuid):
  if not session.has_key('user'):
    return jsonify(error = 'not authorized')
  resultdir = '{}/results/{}'.format(recastconfig.config['RECASTSTORAGEPATH'],request_uuid)
  print 'setting celery app as current'
  celery_app.set_current()

  print 'uploading from rootdir: {}'.format(resultdir)
  asynctasks.uploadallzenodo.delay(resultdir,request_uuid)
  return jsonify(depositionid = 123)

