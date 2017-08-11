# must be loaded first so that env vars get set
import recastconfig
import json
import os
import logging
import importlib
import pkg_resources
import yaml
import requests
import time

import socketio
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, session, url_for



from recast_interface_blueprint import recast
import recastbackend.resultaccess
import recastbackend.jobdb
from recastbackend import wflowapi as wflowapi

log = logging.getLogger(__name__)

def get_blueprint(name):
    module, attr = name.split(':')
    blueprintmodule = importlib.import_module(module)
    return getattr(blueprintmodule, attr)


def create_app(config=None):
    templates_path = pkg_resources.resource_filename(
        'recastcontrolcenter', 'templates')
    static_path = pkg_resources.resource_filename(
        'recastcontrolcenter', 'static')
    app = Flask('RECAST-demo',
                template_folder=templates_path,
                static_folder=static_path)
    app.config.from_object('recastcontrolcenter.admin.default_config')
    if config:
        app.config.from_object(config)
    app.register_blueprint(recast, url_prefix='/recast')


    return app

flask_app = create_app()


sio = socketio.Server(logger=True, async_mode='gevent')
flask_app.wsgi_app = socketio.Middleware(sio, flask_app.wsgi_app)



from flask_oauth import OAuth
oauth = OAuth()
oauth_app = oauth.remote_app('oauth_app',
                             base_url=None,
                             request_token_url=None,
                             access_token_url=recastconfig.config[
                                 'RECAST_OAUTH_TOKENURL'],
                             authorize_url=recastconfig.config[
                                 'RECAST_OAUTH_AUTHORIZEURL'],
                             consumer_key=recastconfig.config[
                                 'RECAST_OAUTH_APPID'],
                             consumer_secret=recastconfig.config[
                                 'RECAST_OAUTH_SECRET'],
                             request_token_params={
                                 'response_type': 'code', 'scope': 'bio'},
                             access_token_params={
                                 'grant_type': 'authorization_code'},
                             access_token_method='POST'
                             )



def user_data(access_token):
    r = requests.get(
        'https://oauthresource.web.cern.ch/api/Me',
        headers={'Authorization': 'Bearer {}'.format(access_token)}
    )
    return r.json()


def extract_user_info(userdata):
    userjson = {'experiment': 'unaffiliated'}

    egroup_to_expt = {
        'cms-members': 'CMS',
        'alice-member': 'ALICE',
        'atlas-active-members-all': 'ATLAS',
        'lhcb-general': 'LHCb'
    }

    for x in userdata:
        if x['Type'] == 'http://schemas.xmlsoap.org/claims/Firstname':
            userjson['firstname'] = x['Value']
        if x['Type'] == 'http://schemas.xmlsoap.org/claims/Lastname"':
            userjson['lastname'] = x['Value']
        if x['Type'] == 'http://schemas.xmlsoap.org/claims/CommonName':
            userjson['username'] = x['Value']
        if x['Type'] == 'http://schemas.xmlsoap.org/claims/Group':
            if x['Value'] in egroup_to_expt:
                userjson['experiment'] = egroup_to_expt[x['Value']]
    return userjson


@flask_app.route(recastconfig.config['RECAST_OAUTH_REDIRECT_ROUTE'])
@oauth_app.authorized_handler
def oauth_redirect(resp):
    next_url = request.args.get('next') or url_for('home')
    if resp is None:
        return redirect(next_url)

    data = user_data(resp['access_token'])
    session['user'] = extract_user_info(data)

    return redirect(next_url)


@flask_app.route('/login')
def login():

    if recastconfig.config.get('RECAST_DUMMY_LOGIN',False):
        next_url = request.args.get('next') or url_for('home')
        session['user'] = {
            'firstname': 'Lukas',
            'lastname': 'Heinrich',
            'username': 'lheinric_dummy',
            'experiment': 'ATLAS'
        }
        return redirect(next_url)  
    redirect_uri = recastconfig.config['RECAST_BASEURL'] + url_for('oauth_redirect')
    return oauth_app.authorize(callback=redirect_uri)


@flask_app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/')

#
# these are the views
#

@flask_app.route("/")
def home():
    if recastconfig.config['RECAST_OAUTH_DUMMYLOGIN']:
        if('user' in session):
            session.pop('user')
        session['user'] = {'username': 'dummyuser'}
        userinfo = session.get('user', {})
        print('userinfo: {}'.format(userinfo))
    return render_template('home.html')


@flask_app.route('/status/<basicreqid>')
def request_point_status(basicreqid):
    resultdir = recastbackend.resultaccess.basicreqpath(basicreqid)
    available = os.path.exists(resultdir)
    response = {'available': available, 'ready_wflowconfigs': []}
    if available:
        response['ready_wflowconfigs'] = os.listdir(
            recastbackend.resultaccess.basicreqpath(basicreqid))
    return jsonify(**response)


@flask_app.route('/resultfile/<basicreqid>/<wflowconfigname>/<path:filepath>')
def resultfile(basicreqid, wflowconfigname, filepath):
    fullpath = recastbackend.resultaccess.resultfilepath(
        basicreqid, wflowconfigname, filepath)
    return send_from_directory(os.path.dirname(fullpath), os.path.basename(fullpath))

backendconfig = yaml.load(pkg_resources.resource_stream(
    'recastcontrolcenter', 'resources/backendconfig.yml'))
for resultviewconfig in backendconfig['blueprintconfig']:
    blueprint = get_blueprint(resultviewconfig['blueprint'])
    flask_app.register_blueprint(blueprint, url_prefix='/{}'.format(
        resultviewconfig['prefix']
    ))


from recastbackend.catalogue import recastcatalogue
default_views_for_plugin = {x['plugin']: x['blueprint'] for x in backendconfig['defaultviews']}

@flask_app.route('/resultview/<analysisid>/<wflowconfigname>/<basicreqid>')
def resultview(basicreqid, analysisid, wflowconfigname):
    plugin = recastcatalogue()[int(analysisid)][wflowconfigname]['wflowplugin']
    blueprintname = get_blueprint(default_views_for_plugin[plugin]).name
    return redirect(url_for('{}.result_view'.format(blueprintname), analysisid=analysisid, basicreqid=basicreqid, wflowconfigname=wflowconfigname))


@flask_app.route('/monitor/<workflow_id>')
def monitorview(workflow_id):
    return render_template('monitor.html', workflow_id=workflow_id)

@flask_app.route('/backend')
def backendstatusview():
    job_info = [{'jobguid': k, 'details': v} for k,v in recastbackend.jobdb.jobs_details(recastbackend.jobdb.all_jobs()).iteritems()]
    return render_template('job_status.html', job_info = job_info)

def background_thread():
    """Example of how to send server generated events to clients."""
    log.info('starting background thread')
    for msg in wflowapi.log_msg_stream():
        time.sleep(0.01)
        log.info('HELLO {}'.format(msg))
        if msg['msg_type'] in ['wflow_log','wflow_state']:
            try:
                sio.emit('room_msg', msg, room=msg['wflowguid'], namespace='/wflow')
            except:
                log.exception('something went wrong in message handling')
                pass
        if msg['msg_type'] == 'simple_log':
            sio.emit('log_message', msg, room = msg['jobguid'], namespace = '/subjobmon')

@sio.on('connect', namespace='/wflow')
def connect(sid, environ):
    print('Client connected to /wflow')


@sio.on('join', namespace='/wflow')
def enter(sid, data):
    print('data', data)

    states = wflowapi.get_workflow_messages(data['room'],topic = 'state')
    try:
        sio.emit('room_msg', states[-1], room=sid, namespace='/wflow')
    except IndexError:
        pass

    stored_messages = wflowapi.get_workflow_messages(data['room'], topic = 'log')
    for msg in stored_messages:
        sio.emit('room_msg', msg, room=sid, namespace='/wflow')

    print('Adding Client {} to room {}'.format(sid, data['room']))
    sio.enter_room(sid, data['room'], namespace='/wflow')

@sio.on('roomit', namespace='/wflow')
def roomit(sid, data):
    print('Emitting to Room: {}'.format(data['room']))
    sio.emit('join_ack', {'data':'Welcome a new member to the room {}'.format(data['room'])}, room=data['room'], namespace='/wflow')

@sio.on('disconnect', namespace='/wflow')
def disconnect(sid):
    print('Client disconnected')


