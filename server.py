import gevent
from gevent import monkey; monkey.patch_all()

from flask import Flask, render_template, request, jsonify, send_from_directory

from socketio.namespace import BaseNamespace
from socketio import socketio_manage
from celery.result import BaseAsyncResult

import uuid
import os

app = Flask(__name__)

app.debug = True

import redis

import IPython
import time
import sqlite3


import msgpack

from socketio.mixins import RoomsMixin

class MonitoringNamespace(BaseNamespace,RoomsMixin):
  # def subscriber(self):
  #   print "subscribing to redis socket.io#emitter"
  #   red = redis.StrictRedis(host = 'localhost', db = 0)
  #   pubsub = red.pubsub()
  #   pubsub.subscribe('socket.io#emitter')
  #   self.emit('subscribed')
  #
  #
  #   for m in pubsub.listen():
  #     # print m
  #     if m['type'] == 'message':
  #       data =  msgpack.unpackb(m['data'])[0]
  #       extras =  msgpack.unpackb(m['data'])[1]
  #
  #       # print 'msgpack payload: {}'.format(data)
  #       # print 'msgpack extras: {}'.format(extras)
  #
  #       if(data['nsp'] == '/monitor'):
  #
  #         if(extras['rooms']):
  #           for room in extras['rooms']:
  #             roomdata = [room]+data['data']
  #             print 'emitting to room {}'.format(roomdata)
  #             self.emit_to_room(*roomdata)
  #         else:
  #           print "emitting {}".format(data['data'])
  #           self.emit(*data['data'])
  #
  def on_subscribe(self,msg):
    pass#self.spawn(self.subscriber)

  def on_join(self,data):
    print "joining room: {}".format(data['room'])
    self.join(data['room'])
    self.join("myRoom")
    self.emit('joined')


  def luke_emit_to_room(self, room, event, *args):
    """This is sent to all in the room (in this particular Namespace)"""
    pkt = dict(type="event",name=event,args=[],endpoint=self.ns_name)

    room_name = self._get_room_name(room)

    print 'room name would be: {}'.format(room_name)

    for sessid, socket in self.socket.server.sockets.iteritems():
      if room_name in socket.session['rooms']:
        socket.send_packet(pkt)


  def puke_emit_to_room(self, room, event, *args):
    """This is sent to all in the room (in this particular Namespace)"""
    pkt = dict(type="event",name=event,args=[],endpoint=self.ns_name)
    room_name = self._get_room_name(room)

    print 'room name would be: {}'.format(room_name)

    for sessid, socket in self.socket.server.sockets.iteritems():
      print socket
      print self.socket
      notsame = (socket != self.socket)
      roompresent = (room_name in socket.session['rooms'])

      print "rooms: {}".format(socket.session['rooms'])
      print "notsame: {}, room present: {}".format(notsame,roompresent)

      if room_name in socket.session['rooms'] and self.socket != socket:
        print "sending packet"
        socket.send_packet(pkt)
        # gevent.sleep(0)
      print '---'

  def on_emitToRoom(self,data):
    print "emitting to room: {}".format(data['room'])
    self.puke_emit_to_room(data['room'],'room_msg','hello')



  def on_emitToAll(self):
    print "emitting to all"
    self.emit('room_msg','hello')


from recast_interface_blueprint import recast

app.register_blueprint(recast, url_prefix='/recast')

from rivet_blueprint import rivetblue
app.register_blueprint(rivetblue, url_prefix='/rivet')

# from general_rivet_blueprint import blueprint as rivetresultblue
# app.register_blueprint(rivetresultblue, url_prefix='/rivetresult')

from catalogue import implemented_analyses

for analysis_uuid,data in implemented_analyses.iteritems():
  app.register_blueprint(data['blueprint'], url_prefix='/'+analysis_uuid)
  
#
# these are the views  
#
@app.route("/")
def home():
    return render_template('home.html')

@app.route('/status/<requestId>')
def request_status(requestId):
  resultdir = 'results/{}'.format(requestId)
  available = os.path.exists(resultdir)
  return jsonify(resultsAvailable=available)

@app.route('/status/<requestId>/<parameter_pt>')
def request_point_status(requestId,parameter_pt):
  resultdir = 'results/{}/{}'.format(requestId,parameter_pt)
  available = os.path.exists(resultdir)
  return jsonify(resultsAvailable=available)

@app.route('/resultfile/<requestId>/<parameter_pt>/<path:file>')
def plots(requestId,parameter_pt,file):
  filepath = 'results/{}/{}/{}'.format(requestId,parameter_pt,file)
  return send_from_directory(os.path.dirname(filepath),os.path.basename(filepath))


@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    # print request.environ
    socketio_manage(request.environ, {
        '/monitor': MonitoringNamespace
    })
    return app.response_class()

from socketio.server import SocketIOServer, serve

if __name__ == "__main__":
  serve(app, port = 5000, host = '0.0.0.0')
