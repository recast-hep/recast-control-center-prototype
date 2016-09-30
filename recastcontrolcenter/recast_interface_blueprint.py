import json
import requests
import os
import uuid
import glob
import zipfile
import pickle
import pkg_resources
import recastconfig
import importlib
from flask import Blueprint, render_template, jsonify, request, session
import recastcontrolcenter.backendtasks as asynctasks
from recastbackend.catalogue import recastcatalogue
import recastbackend.resultextraction

import logging
log = logging.getLogger(__name__)

celery_app  = importlib.import_module(recastconfig.config['RECAST_CELERYAPP']).app
celery_app.set_current()

import recastapi.request.read
import recastapi.analysis.read
import recastbackend.jobstate
import recastapi.response.write

recast = Blueprint('recast', __name__, template_folder='recast_interface_templates')

@recast.route('/request/<int:reqid>')
def recast_request_view(reqid):
  request_info = recastapi.request.read.scan_request(reqid)

  analysis_id = recastapi.request.read.scan_request(reqid)['analysis_id']
  analysis_info = recastapi.analysis.read.analysis(analysis_id)

  parpoints = recastapi.request.read.point_request_of_scan(reqid)
  basic_req_data = {
    p['id']:recastapi.request.read.basic_request_of_point(p['id'])
        for p in parpoints
  }

  wflow_config_labels = recastcatalogue().get(int(analysis_id),{}).keys()
  from recastbackend.jobstate import get_flattened_jobs
  processing_info = {}
  for k,v in basic_req_data.iteritems():
      for basic_req in v:
          print 'basic_req',basic_req
          processing_info[basic_req['id']] = get_flattened_jobs(celery_app,basic_req['id'],wflow_config_labels)

  log.info('proc info is %s',processing_info)

  return render_template('recast_request.html', request_info  = request_info,
                                                parpoints = enumerate(parpoints),
                                                basic_req_data = basic_req_data,
                                                analysis_info = analysis_info,
                                                wflow_configs      = wflow_config_labels,
                                                processing_info   = processing_info)

@recast.route('/requests')
def recast_requests_view():
    requests_info = recastapi.request.read.scan_request()

    wflow_config_data = {}

    full_configs = recastcatalogue()
    print full_configs
    for req in requests_info:
        identifier = req['analysis_id']
        labels = [] if identifier not in full_configs else full_configs[identifier].keys()
        wflow_config_data[req['id']] = labels

    print wflow_config_data
    return render_template('recast_all_requests.html',
        requests_info = reversed(requests_info),
        wflow_config_data = wflow_config_data
    )

@recast.route('/processBasicRequest', methods=['GET'])
def process_request_point():
    wflowconfig = request.args['wflowconfig']
    analysisid  = request.args['analysisid']
    basicreqid = request.args['basicreqid']

    from recastbackend.submission import submit_recast_request
    jobguid,result = submit_recast_request(basicreqid,analysisid,wflowconfig)

    log.info('jobguid is: %s, celery id is: %s',jobguid,result)
    return jsonify(jobguid=jobguid)


def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file),os.path.join(root, file).split('/',2)[-1])

def prepareupload(fullpath):
    stagingarea = '{}/stagingarea'.format(os.environ['RECAST_STORAGEPATH'])
    if not os.path.exists(stagingarea):
        os.makedirs(stagingarea)
    zipfilename = '{}/uploadfile_{}.zip'.format(stagingarea,uuid.uuid4())
    zipdir(fullpath,zipfile.ZipFile(zipfilename,'w'))
    return zipfilename


@recast.route('/uploadPointResponse')
def uploadresults():
    if not session.has_key('user'):
        return jsonify(error = 'not authorized')
    scanreqid = request.args['scanreqid']
    fullpath = recastbackend.resultaccess.basicreq_wflowconfigpath(request.args['basicreqid'],request.args['wflowconfig'])
    zipfilename = prepareupload(fullpath)
    scan_response = recastapi.response.write.scan_response(scanreqid)
    resultdata = recastbackend.resultextraction.extract_result(fullpath,scanreqid,request.args['wflowconfig'])
    point_response = recastapi.response.write.point_response(scan_response['id'], request.args['pointreqid'], resultdata)
    recastapi.response.write.basic_response_with_archive(point_response['id'], request.args['basicreqid'], zipfilename, resultdata)
    return jsonify(sucess = 'ok', resultdata = resultdata)
