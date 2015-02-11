import gevent
from gevent import monkey; monkey.patch_all()

from flask import Flask, render_template, request, jsonify, send_from_directory,redirect, session

from socketio.namespace import BaseNamespace
from socketio import socketio_manage
from celery.result import BaseAsyncResult

import uuid
import os

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

from flask_sso import SSO
ext = SSO(app=app)

@ext.login_handler
def login(user_info):
  session['user'] = user_info
  return redirect('/')

@app.route('/logout')
def logout():
  session.pop('user')
  return redirect('/')



app.debug = True

import redis

import IPython
import time
import sqlite3


import msgpack

from socketio.mixins import RoomsMixin

class MonitoringNamespace(BaseNamespace,RoomsMixin):
  def subscriber(self):
    print "subscribing to redis socket.io#emitter"
    red = redis.StrictRedis(host = 'localhost', db = 0)
    pubsub = red.pubsub()
    pubsub.subscribe('socket.io#emitter')
    self.emit('subscribed')

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
    
  def on_subscribe(self):
    self.spawn(self.subscriber)

  def on_helloServer(self):
    print "hello back"
    self.emit('plainEmit')
    print "emitting to room"


  def on_join(self,data):
    print "joining room: {}".format(data['room'])
    self.join(data['room'])

    self.emit('joined')

  def on_emitToRoom(self,data):
    print "emitting to room: {} and myself".format(data['room'])
    self.emit('room_msg',data['msg']) 
    self.emit_to_room(data['room'],'room_msg',data['msg'])


from recast_interface_blueprint import recast

app.register_blueprint(recast, url_prefix='/recast')

from rivet_blueprint import rivetblue
app.register_blueprint(rivetblue, url_prefix='/rivet')

from recastrivet.general_rivet_blueprint import blueprint as rivetresultblue
app.register_blueprint(rivetresultblue, url_prefix='/rivetresult')

from catalogue import implemented_analyses

for analysis_uuid,data in implemented_analyses.iteritems():
  app.register_blueprint(data['blueprint'], url_prefix='/'+analysis_uuid)
  
#
# these are the views  
#
@app.route("/")
def home():
    # if(session.has_key('user')): session.pop('user')
    # session['user'] =  {'username':'lukas'}
    userinfo = session.get('user',{})
    return render_template('home.html', userinfo = userinfo)

@app.route("/rivet")
def rivethome():
    return render_template('rivethome.html')

RECASTSTORAGEPATH = '/home/analysis/recast/recaststorage'

@app.route('/status/<requestId>')
def request_status(requestId):
  resultdir = '{}/results/{}'.format(RECASTSTORAGEPATH,requestId)
  available = os.path.exists(resultdir)
  return jsonify(resultsAvailable=available)

@app.route('/status/<requestId>/<parameter_pt>')
def request_point_status(requestId,parameter_pt):
  resultdir = '{}/results/{}'.format(RECASTSTORAGEPATH,requestId)
  available = os.path.exists(resultdir)
  return jsonify(resultsAvailable=available)

@app.route('/resultfile/<requestId>/<parameter_pt>/<path:file>')
def plots(requestId,parameter_pt,file):
  filepath = '{}/results/{}/{}/{}'.format(RECASTSTORAGEPATH,requestId,parameter_pt,file)
  return send_from_directory(os.path.dirname(filepath),os.path.basename(filepath))

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

from socketio.server import SocketIOServer, serve

if __name__ == "__main__":
  serve(app, port = 8000, host = '0.0.0.0')
