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
import recastcontrolcenter.asynctasks as asynctasks

recast = Blueprint('recast', __name__, template_folder='recast_interface_templates')

RECASTAPIBASEURL = recastapi.BASEURL.rstrip('/')
print 'using URL',recastapi.BASEURL


@recast.route('/request/<uuid>')
def recast_request_view(uuid):
    request_info = requests.get('{}/requests?where=uuid=="{}"'.format(RECASTAPIBASEURL,uuid)).json()['_items']
    assert len(request_info)==1
    request_info=request_info[0]
    analysis_info = recastapi.analysis.analysis(request_info['analysis_id'])
    
    points = requests.get('{}/point_requests?where=scan_request_id=="{}"'.format(RECASTAPIBASEURL,request_info['id'])).json()['_items']
    
    basic_requests = []
    for p in points:
        basic_requests += [requests.get('{}/basic_requests?where=point_request_id=="{}"'.format(RECASTAPIBASEURL,p['id'])).json()['_items']]
    
    points_and_requests = zip(points,basic_requests)
    return render_template('recast_request.html', request_info  = request_info, points_and_requests = points_and_requests, analysis_info = analysis_info)

@recast.route('/requests')
def recast_requests_view():
    requests_info = recastapi.request.request()
    return render_template('recast_all_requests.html', requests_info = requests_info)

@recast.route('/processBasicRequest/<basic_request_id>', methods=['POST','GET'])
def process_request_point(request_uuid,point):
    print 'processing basic request with id: {}'.format(basic_request_id)
    backend = request.args['backend']


@recast.route('/updateResponse/<request_uuid>')
def uploadresults(request_uuid):
    if not session.has_key('user'):
        return jsonify(error = 'not authorized')
    print 'updating response'

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

