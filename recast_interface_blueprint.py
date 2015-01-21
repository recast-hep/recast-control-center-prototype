from flask import Blueprint, render_template, jsonify, request
recast = Blueprint('recast', __name__, template_folder='recast_interface_templates')


import json
import requests
import requests
import os
from zipfile import ZipFile
import glob

import recastapi.request 
import recastapi.analysis 

from catalogue import implemented_analyses

@recast.route('/newrequest')
def new_recast_request():
  analyses = recastapi.analysis.analysis()
  analyses = [a for a in analyses if a['uuid'] in implemented_analyses]
  return render_template('recast_new_request.html', analyses = analyses)

@recast.route('/request/<uuid>')
def recast_request_view(uuid):
  request_info = recastapi.request.request(uuid)
  return render_template('recast_request.html', request_info = request_info)

@recast.route('/requests')
def recast_requests_view():
  requests_info = recastapi.request.request()
  return render_template('recast_all_requests.html', requests_info = requests_info)

@recast.route('/analysis/<uuid>')
def recast_analysis_view(uuid):
  analysis_info = recastapi.analysis.analysis(uuid)
  return render_template('recast_analysis.html', analysis_info = analysis_info)

@recast.route('/analyses')
def recast_analyses_view():
  analyses_info = recastapi.analysis.analysis()
  return render_template('recast_all_analyses.html', analyses_info = analyses_info)

@recast.route('/analysis_status/<analysis_uuid>')
def status(analysis_uuid):
  available =  (analysis_uuid in implemented_analyses)
  return jsonify(analysisImplemented=available)


@recast.route('/upload',methods = ['POST','GET'])
def upload():
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

  zippedfile = '{}/my.zip'.format(uploaddir)
  with ZipFile(zippedfile,'w') as zipfile:
    for file in glob.glob('{}/*'.format(uploaddir)):
      if(os.path.basename(file)!=os.path.basename(zippedfile)):
	zipfile.write(file,os.path.basename(file))

  r = recastapi.request.add_parameter_point(requestuuid,username,description,nevents,xsec,zippedfile)
  
  json.loads(r.content)==request.form['request_uuid']  
  return jsonify(success='ok')

@recast.route('/createRequest', methods=['GET','POST'])
def create_request():
  print 'hello'
  r = recastapi.request.create(request.form['username'],
                               request.form['analysis-uuid'],
                               request.form['model-type'],
                               request.form['title'],
                               request.form['predefined-model'],
                               reason = 'because we can',
                               audience = 'all',
                               activate = True,
                               subscribers = ['lheinric'])
  print 'done'
  return jsonify(requestId = json.loads(r.content))
  
def find_beginning(result):
    if result.parent is None: return result
    return find_beginning(result.parent)
    
@recast.route('/processRequestPoint/<request_uuid>/<point>', methods=['POST','GET'])
def process_request_point(request_uuid,point):
  print "hello"
  request_info = recastapi.request.request(request_uuid)

  if not request_info['analysis-uuid'] in implemented_analyses:
    print "analysis not implemented!"
    raise NotImplementedError

  jobguid, chain = implemented_analyses[request_info['analysis-uuid']]['workflow'].get_chain(request_uuid,point)

  print chain
   
  result = chain.apply_async()

  return jsonify(jobguid=jobguid, task_ids = ['list of task ids']) 
  
  
def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file),os.path.join(root, file).split('/',2)[-1])
       
import recastapi.response
import zipfile
@recast.route('/updateResponse/<request_uuid>')
def uploadresults(request_uuid):
  resultdir = 'results/{}'.format(request_uuid)
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
