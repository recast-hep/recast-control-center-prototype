import gevent
from gevent import monkey; monkey.patch_all()

import uuid
import os
import redis
import time
import sqlite3
import msgpack
import importlib
import json
import recastapi
import json

from flask import Flask, render_template, request, jsonify, send_from_directory,redirect, session, url_for
from flask_sso import SSO

from socketio.namespace import BaseNamespace
from socketio import socketio_manage
from socketio.server import SocketIOServer, serve

from celery.result import BaseAsyncResult

from socketio.mixins import RoomsMixin

import celery
import recastbackend.messaging

#needed to get redis connection working
from recastbackend.productionapp import app as celery_app

####
# blueprints
####

#general recast views
from recast_interface_blueprint import recast

#list of dedicated backends that includes blueprint information
from recastbackend.catalogue import all_backend_catalogue

def get_blueprint(name):
  module,attr = name.split(':')
  blueprintmodule = importlib.import_module(module)  
  return getattr(blueprintmodule,attr)


app = Flask('RECAST-demo')
app.secret_key = 'somesecret'


# Map SSO attributes from ADFS to session keys under session['user']
SSO_ATTRIBUTE_MAP = {
  'HTTP_ADFS_LOGIN': (True, 'username'),
  #'ADFS_LOGIN': (True, 'username'),
  #'ADFS_FULLNAME': (True, 'fullname'),
  #'ADFS_PERSONID': (True, 'personid'),
  #'ADFS_DEPARTMENT': (True, 'department'),
  #'ADFS_EMAIL': (True, 'email')
  # There are other attributes available
  # Inspect the argument passed to the login_handler to see more
  # 'ADFS_AUTHLEVEL': (False, 'authlevel'),
  # 'ADFS_GROUP': (True, 'group'),
  # 'ADFS_ROLE': (False, 'role'),
  # 'ADFS_IDENTITYCLASS': (False, 'external'),
  # 'HTTP_SHIB_AUTHENTICATION_METHOD': (False, 'authmethod'),
  }
app.config.setdefault('SSO_ATTRIBUTE_MAP', SSO_ATTRIBUTE_MAP)
app.config.setdefault('SSO_LOGIN_URL', '/login')

ext = SSO(app=app)

@ext.login_handler
def login(user_info):
  session['user'] = user_info
  return redirect('/')

@app.route('/logout')
def logout():
  session.pop('user')
  return redirect('/')

class MonitoringNamespace(BaseNamespace,RoomsMixin):
  def subscriber(self):
    print "subscribing to redis socket.io#emitter"
    red = redis.StrictRedis(host = 'localhost', db = 0)
    pubsub = red.pubsub()
    pubsub.subscribe('socket.io#emitter')
    self.emit('subscribed')

    #currently we have a specific setup where we want to get the backlog of jobs
    #not a general socketio setup with arbitrary rooms

    assert len(self.session['rooms'])==1
    celery_app.set_current()

    assert celery.current_app == celery_app
    
    print "getting stored messages for room {}".format(self.jobguid)
    stored = recastbackend.messaging.get_stored_messages(self.jobguid)

    print "got {}".format(stored)

    for m in stored:
      old_msg_data =  json.loads(m)
      print old_msg_data

      for_emit = ['room_msg', old_msg_data]
      self.emit(*for_emit)
                    
    for m in pubsub.listen():
      # print m
      if m['type'] == 'message':
        data =  msgpack.unpackb(m['data'])[0]
        extras =  msgpack.unpackb(m['data'])[1]

        print 'msgpack payload: {}'.format(data)
        print 'msgpack extras: {}'.format(extras)
        #
        #
        # print 'NB: self rooms are {}'.format(self.session['rooms'])
        #
        if(data['nsp'] == '/monitor'):
          if(extras['rooms']):
            for room in extras['rooms']:
              #if this socket joined the room this message is sent to emit to it
              #this is a small workaround since every client has one of these
              #redis subscriptions so emit_to_room would result into multiple msgs
              #being sent
              if(self._get_room_name(room) in self.session['rooms']):
                self.emit(*data['data'])
          else:
              self.emit(*data['data'])
    
  def on_helloServer(self):
    print "hello back"
    self.emit('plainEmit')
    print "emitting to room"

  def on_subscribe(self):
    print "not doing much on subscribe"
    
  def on_join_recast_jobguid(self,data):
    print "joining room: {}".format(data['room'])

    self.jobguid = data['room']

    self.join(data['room'])

    self.emit('joined')

    #only spawn listener after join
    self.spawn(self.subscriber)

  def on_emitToRoom(self,data):
    print "emitting to room: {} and myself".format(data['room'])
    self.emit('room_msg',data['msg']) 
    self.emit_to_room(data['room'],'room_msg',data['msg'])


app.register_blueprint(recast, url_prefix='/recast')

for backend,analysis_list in all_backend_catalogue.iteritems():
  for analysis_uuid,data in analysis_list.iteritems():
    blueprint = get_blueprint(data['blueprint'])
    app.register_blueprint(blueprint, url_prefix='/'+analysis_uuid)
  
#
# these are the views  
#
@app.route("/")
def home():
    # if(session.has_key('user')): session.pop('user')
    # session['user'] =  {'username':'lukas'}
    userinfo = session.get('user',{})
    return render_template('home.html', userinfo = userinfo)

RECASTSTORAGEPATH = '/home/analysis/recast/recaststorage'
@app.route('/status/<requestId>')
def request_overall_status(requestId):
  resultdir = '{}/results/{}'.format(RECASTSTORAGEPATH,requestId)
  available = os.path.exists(resultdir)
  return jsonify(resultsAvailable=available)

@app.route('/status/<requestId>/<parameter_pt>')
def request_point_status(requestId,parameter_pt):
  backend = request.args['backend']
  assert backend
  resultdir = '{}/results/{}/{}/{}'.format(RECASTSTORAGEPATH,requestId,parameter_pt,backend)
  available = os.path.exists(resultdir)
  return jsonify(resultsAvailable=available)

@app.route('/resultfile/<requestId>/<parameter_pt>/<path:file>')
def plots(requestId,parameter_pt,file):
  filepath = '{}/results/{}/{}/{}'.format(RECASTSTORAGEPATH,requestId,parameter_pt,file)
  return send_from_directory(os.path.dirname(filepath),os.path.basename(filepath))

@app.route('/resultview/<requestId>/<parameter_pt>/<backend>')
def resultview(requestId,parameter_pt,backend):
  request_info = recastapi.request.request(requestId)
  analysis_uuid = request_info['analysis-uuid']

  blueprintname = get_blueprint(all_backend_catalogue[backend][analysis_uuid]['blueprint']).name
  print url_for('{}.result_view'.format(blueprintname),requestId=requestId,parameter_pt=parameter_pt)
  return redirect(url_for('{}.result_view'.format(blueprintname),requestId=requestId,parameter_pt=parameter_pt))


@app.route('/monitor/<jobguid>')
def monitorview(jobguid):
  return render_template('monitor.html', jobguid = jobguid)

@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    print "socket io route called"
    socketio_manage(request.environ, {
        '/monitor': MonitoringNamespace
    })
    return app.response_class()

def do_serve():
  serve(app, port = 8000, host = '0.0.0.0', transports = 'xhr-polling')

if __name__ == '__main__':
  do_serve()