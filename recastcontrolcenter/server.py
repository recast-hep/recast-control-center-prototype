# must be loaded first so that env vars get set
import recastconfig
import json
import os
import importlib
import pkg_resources
import yaml

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, session, url_for
from socketio import socketio_manage
from socketapp import MonitoringNamespace
from recast_interface_blueprint import recast

import recastbackend.resultaccess
import recastbackend.jobdb
from recastdb.database import db


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
    db.init_app(app)
    return app

flask_app = create_app()


from flask_oauth import OAuth
oauth = OAuth()
oauth_app = oauth.remote_app('oauth_app',
                             base_url=None,
                             request_token_url=None,
                             access_token_url=recastconfig.config[
                                 'RECAST_OAUTH_TOKENURL'],
                             authorize_url=recastconfig.config[
                                 'RECAST_OAUTUH_AUTHORIZEURL'],
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

import requests


def user_data(access_token):
    r = requests.get(
        'https://oauthresource.web.cern.ch/api/Me',
        headers={'Authorization': 'Bearer {}'.format(access_token)}
    )
    return r.json()


@flask_app.route(recastconfig.config['RECAST_OAUTH_REDIRECT_ROUTE'])
@oauth_app.authorized_handler
def oauth_redirect(resp):
    global session_store

    next_url = request.args.get('next') or url_for('home')
    if resp is None:
        return redirect(next_url)

    # session['access_token'] = resp['access_token']
    data = user_data(resp['access_token'])
    session['user'] = {}

    for x in data:
        if x['Type'] == 'http://schemas.xmlsoap.org/claims/Firstname':
            session['user']['firstname'] = x['Value']
        if x['Type'] == 'http://schemas.xmlsoap.org/claims/Lastname"':
            session['user']['lastname'] = x['Value']
        if x['Type'] == 'http://schemas.xmlsoap.org/claims/CommonName':
            session['user']['username'] = x['Value']

    return redirect(next_url)
    # return '<a href=https://recast-control.cern.ch/>HOME</a>'
    # return redirect('/whaaat')


@flask_app.route('/login')
def login():
    redirect_uri = recastconfig.config[
        'RECAST_BASEURL'] + url_for('oauth_redirect')
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
        if(session.has_key('user')):
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
default_views_for_plugin = {x['plugin']: x['blueprint']
                            for x in backendconfig['defaultviews']}


@flask_app.route('/resultview/<analysisid>/<wflowconfigname>/<basicreqid>')
def resultview(basicreqid, analysisid, wflowconfigname):
    plugin = recastcatalogue()[int(analysisid)][wflowconfigname]['wflowplugin']
    blueprintname = get_blueprint(default_views_for_plugin[plugin]).name
    return redirect(url_for('{}.result_view'.format(blueprintname), analysisid=analysisid, basicreqid=basicreqid, wflowconfigname=wflowconfigname))


@flask_app.route('/monitor/<jobguid>')
def monitorview(jobguid):
    return render_template('monitor.html', jobguid=jobguid)

@flask_app.route('/backend')
def backendstatusview():
    job_info = [{
        'jobguid': x,
        'details': recastbackend.jobdb.job_details(x)
    } for x in recastbackend.jobdb.all_jobs()]
    return render_template('job_status.html', job_info = job_info)

@flask_app.route('/sandbox')
def sandbox():
    # get possibly preset values
    print request.args
    presets = {}
    presets['toplevel'] = request.args.get('toplevel', None)
    presets['workflow'] = request.args.get('workflow', None)
    presets['outputs'] = request.args.get('outputs', None)
    presets['archive'] = request.args.get('archive', None)
    presets['pars'] = json.dumps(json.loads(request.args.get('pars', '{}')))
    presets = {k: v for k, v in presets.iteritems() if v is not None}

    return render_template('sandbox.html', presets=presets)


@flask_app.route('/sandbox_submit', methods=['POST'])
def sandbox_submit():
    from recastbackend.submission import yadage_submission
    data = request.json
    print data
    ctx, result = yadage_submission(
        configname=data['wflowname'],
        outputdir=os.path.join(os.environ['RECAST_RESULT_BASE'], 'sandbox'),
        input_url=data['inputURL'],
        outputs=data['outputs'].split(','),
        toplevel=data['toplevel'],
        workflow=data['workflow'],
        presetpars=data['preset_pars'],
        queue='recast_yadage_queue',
    )
    print 'submitted ctx from sandbox!', ctx
    return jsonify({'jobguid': ctx['jobguid']})


@flask_app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    socketio_manage(request.environ, {
        '/monitor': MonitoringNamespace
    })
    return flask_app.response_class()
