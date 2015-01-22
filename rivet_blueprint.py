from flask import Blueprint, render_template, jsonify, request, send_from_directory
rivetblue = Blueprint('rivet', __name__, template_folder='rivet_templates')

import rivet
import uuid
import sqlite3
import os
from zipfile import ZipFile
import glob 
analyses = {x:rivet.AnalysisLoader.getAnalysis(x) for x in rivet.AnalysisLoader.analysisNames()}
attrs = ['name','authors','bibTeX','description','experiment','name','bibKey','collider','references','status','year','spiresId','runInfo','summary']
analyses_info = {k:{attrname:getattr(v,attrname)() for attrname in attrs} for k,v in analyses.iteritems()}
analyses_info = {k:v for k,v in analyses_info.iteritems() if (v['collider'] == 'LHC' or 'MC_' in v['name'])}

requests_colnames = ['requestId','analysisId','username','title','predefine-model','model-type']
param_colnames = ['requestId','pointcount','description','file']

@rivetblue.route('/analyses')
def rivet_all_analyses_view():
  return render_template('rivet_all_analyses.html', analyses_info = analyses_info)

@rivetblue.route('/analysis/<rivetID>')
def rivet_analysis_view(rivetID):
  analysis_info = analyses_info[rivetID]
  return render_template('rivet_analysis.html', analysis_info = analysis_info)

@rivetblue.route('/requests')
def rivet_requests_view():
  db = sqlite3.connect('rivetRequests.db')
  requests = db.execute('select * from requests').fetchall()
  db.close()
  requests_info = [dict(zip(requests_colnames,r)) for r in requests]
  return render_template('rivet_all_requests.html', requests_info = requests_info)

@rivetblue.route('/request/<uuid>')
def recast_request_view(uuid):
  db = sqlite3.connect('rivetRequests.db')
  request = db.execute('select * from requests where requestid = "{}"'.format(uuid)).fetchall()

  param_points = db.execute('select * from param_points where requestId == "{}"'.format(uuid)).fetchall()
  db.close()
  assert len(request)
  request_info = dict(zip(requests_colnames,request[0]))

  param_info = [dict(zip(param_colnames,p)) for p in param_points]

  return render_template('rivet_request.html', request_info = request_info, param_info = param_info)

@rivetblue.route('/newrequest')
def rivet_new_request():
  return render_template('rivet_new_request.html', analyses_info = analyses_info)

@rivetblue.route('/createRequest',methods=['POST','GET'])
def rivet_create_request():
  requestId = uuid.uuid1()
  db = sqlite3.connect('rivetRequests.db')
  
  db.execute("INSERT INTO requests VALUES (?,?,?,?,?,?)",[str(requestId),
                                                          request.form['analysis-uuid'],
                                                          request.form['username'],
                                                          request.form['title'],
                                                          request.form['predefined-model'],
                                                          request.form['model-type']])
  db.commit()                                             
  db.close()                                             
  
  return jsonify(requestId = requestId)


import general_rivet_backendtasks
@rivetblue.route('/processRequestPoint/<request_uuid>/<point>', methods=['POST','GET'])
def process_request_point(request_uuid,point):

  print "processing the request"

  db = sqlite3.connect('rivetRequests.db')
  matching = db.execute('select * from param_points where requestId == "{}" and pointcount == {} '.format(request_uuid,point)).fetchall()
  requestrow = db.execute('select * from requests where requestId == "{}"'.format(request_uuid)).fetchall()
  db.close()                                             



  print matching
 
  print requestrow

  assert len(matching)==1
  assert len(requestrow)==1
  
  
  jobinfo = dict(zip(param_colnames,matching[0]))

  print jobinfo
  jobinfo.update({'rivetanalysis':requestrow[0][1]})

  jobguid, chain = general_rivet_backendtasks.get_chain(jobinfo)

  result = chain.apply_async()

  return jsonify(jobguid='123', task_ids = ['list of task ids']) 


@rivetblue.route('/status/<requestId>/<parameter_pt>')
def request_point_status(requestId,parameter_pt):
  resultdir = 'rivet_results/{}/{}'.format(requestId,parameter_pt)
  available = os.path.exists(resultdir)
  return jsonify(resultsAvailable=available)

@rivetblue.route('/upload',methods = ['POST','GET'])
def upload():
  db = sqlite3.connect('rivetRequests.db')
  
  #rudimentary.. better: http://flask.pocoo.org/docs/0.10/patterns/fileuploads/#uploading-files
  mode = request.form.get('mode',None)

  username = request.form['username']
  requestId = request.form['requestId']
  description = request.form['description']

  next_point_ctr = len(db.execute('select * from param_points where requestId == "{}"'.format(requestId)).fetchall())

  
  uploaddir = 'rivet_uploads/{}/{}'.format(requestId,'parameter-{}'.format(next_point_ctr))
  os.makedirs(uploaddir)

  for f in request.files.itervalues(): f.save('{}/{}'.format(uploaddir,f.filename))

  zippedfile = '{}/inputfiles.zip'.format(uploaddir)
  with ZipFile(zippedfile,'w') as zipfile:
    for file in glob.glob('{}/*'.format(uploaddir)):
      if(os.path.basename(file)!=os.path.basename(zippedfile)):
	zipfile.write(file,os.path.basename(file))

  db.execute("INSERT INTO param_points VALUES (?,?,?,?)",[str(requestId),
                                                              next_point_ctr,
                                                              description,
                                                              os.path.basename(zippedfile)
                                                              ])
  db.commit()                                             
  db.close()                                             
  
  return jsonify(success='ok')
  
@rivetblue.route('/inputfile/<requestId>/<parameter_pt>/<filename>')
def serve_inputs(requestId,parameter_pt,filename):
  uploaddir = 'rivet_uploads/{}/{}'.format(requestId,'parameter-{}'.format(parameter_pt))
  return send_from_directory(uploaddir,filename)
  
