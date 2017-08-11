import os
import uuid
import zipfile
from flask import Blueprint, render_template, jsonify, request, session
from recastbackend.catalogue import recastcatalogue
import recastbackend.resultextraction
from recastbackend.jobdb import get_flattened_jobs

import logging
log = logging.getLogger(__name__)

import recastapi.request.read
import recastapi.analysis.read
import recastapi.response.write

recast = Blueprint('recast', __name__, template_folder='recast_interface_templates')

@recast.route('/request/<int:reqid>')
def recast_request_view(reqid):
    request_info = recastapi.request.read.scan_request(reqid)

    analysis_id = recastapi.request.read.scan_request(reqid)['analysis_id']
    analysis_info = recastapi.analysis.read.analysis(analysis_id)

    parpoints = recastapi.request.read.point_request_of_scan(reqid)
    point_coordinates = {
        p['id']: {c['title']:c['value'] for c in p['point_coordinates']}
        for p in parpoints
    }

    basic_req_data = {
        p['id']: p['requests']
        for p in parpoints
    }


    print recastcatalogue()
    wflow_configs = recastcatalogue().get(int(analysis_id), {})

    print wflow_configs,"HHUHUH"
    processing_info = {}
    for k, v in basic_req_data.iteritems():
        for basic_req in v:
            processing_info[basic_req['id']] = get_flattened_jobs(basic_req['id'], wflow_configs.keys())

    visdata = {
        'data': [
            {
              "values": [],
              "name": "pointrequests"
            }
        ],
        'pars': point_coordinates.values()[0].keys()
    }

    for i,p in enumerate(parpoints):
        pd = {}
        pd.update(global_pr_id = p['id'], scan_pr_id=i, **point_coordinates[p['id']])
        visdata['data'][0]['values'].append(pd)
        
    log.info('proc info is %s', processing_info)
    return render_template('recast_request.html',
                            request_info=request_info,
                            visdata = visdata,
                            point_coordinates = point_coordinates,
                            parpoints=enumerate(parpoints),
                            basic_req_data=basic_req_data,
                            analysis_info=analysis_info,
                            wflow_configs=wflow_configs,
                            processing_info=processing_info
                            )


@recast.route('/wflowcatalgue')
def recast_workflow_catalogue_view():
    catalogue_info = [{
            'analysis_id': anaid,
            'analysis_info': recastapi.analysis.read.analysis(anaid),
            'implementations': v.keys()
        } for anaid,v in recastcatalogue().iteritems()
    ]
    return render_template('recast_catalogue.html',
                           catalogue_info = catalogue_info)


@recast.route('/requests')
def recast_requests_view():
    requests_info = recastapi.request.read.scan_request()

    wflow_config_data = {}

    full_configs = recastcatalogue()
    for req in requests_info:
        identifier = req['analysis_id']
        labels = [] if identifier not in full_configs else full_configs[identifier].keys()
        wflow_config_data[req['id']] = labels

    return render_template('recast_all_requests.html',
                           requests_info = reversed(requests_info),
                           wflow_config_data = wflow_config_data
                           )

@recast.route('/processBasicRequest', methods=['GET'])
def process_request_point():
    wflowconfig = request.args['wflowconfig']
    analysisid = request.args['analysisid']
    basicreqid = request.args['basicreqid']

    from recastbackend.submission import submit_recast_request
    jobguid = submit_recast_request(basicreqid, analysisid, wflowconfig)
    log.info('jobguid is: %s', jobguid)
    return jsonify(jobguid=jobguid)

def zipdir(path, zipfile):
    for root, dirs, files in os.walk(path):
        for fl in files:
            zipfile.write(os.path.join(root, fl), os.path.join(
                root, fl).split('/', 2)[-1])

def prepareupload(fullpath):
    stagingarea = '{}/stagingarea'.format(os.environ['RECAST_STORAGEPATH'])
    if not os.path.exists(stagingarea):
        os.makedirs(stagingarea)
    zipfilename = '{}/uploadfile_{}.zip'.format(stagingarea, uuid.uuid4())
    zipdir(fullpath, zipfile.ZipFile(zipfilename, 'w'))
    return zipfilename

@recast.route('/uploadPointResponse')
def uploadresults():
    if not 'user' in session:
        return jsonify(error='not authorized')
    scanreqid = request.args['scanreqid']
    analysisid = recastapi.request.read.scan_request(scanreqid)['analysis_id']
    fullpath = recastbackend.resultaccess.basicreq_wflowconfigpath(
        request.args['basicreqid'], request.args['wflowconfig'])
    zipfilename = prepareupload(fullpath)
    scan_response = recastapi.response.write.scan_response(scanreqid)
    resultdata = recastbackend.resultextraction.extract_result(
        fullpath, analysisid, request.args['wflowconfig'])
    point_response = recastapi.response.write.point_response(
        scan_response['id'], request.args['pointreqid'], resultdata)
    recastapi.response.write.basic_response_with_archive(
        point_response['id'], request.args['basicreqid'], resultdata, request.args['wflowconfig'], zipfilename)
    return jsonify(sucess='ok', resultdata=resultdata)
