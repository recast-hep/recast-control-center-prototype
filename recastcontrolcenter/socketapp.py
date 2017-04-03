# needed to get redis connection working
from socketio.mixins import RoomsMixin
from socketio.namespace import BaseNamespace
import recastbackend.wflowapi
import msgpack
import json

class MonitoringNamespace(BaseNamespace, RoomsMixin):

    def subscriber(self):
        self.emit('subscribed')

        # currently we have a specific setup where we want to get the backlog of jobs
        # not a general socketio setup with arbitrary rooms

        assert len(self.session['rooms']) == 1


        print "getting stored messages for room {}".format(self.jobguid)
        stored = recastbackend.wflowapi.get_stored_messages(self.jobguid)

        connected_msg = {'date': 'connected', 'msg': ''}
        self.emit('room_msg', connected_msg)

        latest_state = None
        for m in stored:
            old_msg_data = json.loads(m)
            for_emit = ['room_msg', old_msg_data]
            if old_msg_data['type'] == 'yadage_stage':
                latest_state = old_msg_data
                continue
            self.emit(*for_emit)
        if latest_state:
            self.emit('room_msg', latest_state)

        for m in recastbackend.wflowapi.log_msg_stream():
            if m['type'] == 'message':
                data = msgpack.unpackb(m['data'])[0]
                extras = msgpack.unpackb(m['data'])[1]

                print 'msgpack payload: {}'.format(data)
                print 'msgpack extras: {}'.format(extras)
                if(data['nsp'] == '/monitor'):
                    if(extras['rooms']):
                        for room in extras['rooms']:
                            # if this socket joined the room this message is sent to emit to it
                            # this is a small workaround since every client has one of these
                            # redis subscriptions so emit_to_room would result into multiple msgs
                            # being sent
                            if(self._get_room_name(room) in self.session['rooms']):
                                self.emit(*data['data'])
                    else:
                        self.emit(*data['data'])

    def on_helloServer(self):
        print "hello back"
        self.emit('plainEmit', {'some': 'data'})
        print "emitting to room"

    def on_subscribe(self):
        print "not doing much on subscribe"

    def on_join_recast_jobguid(self, data):
        print "joining room: {}".format(data['room'])

        self.jobguid = data['room']
        self.join(data['room'])
        self.emit('joined')

        # only spawn listener after join
        self.spawn(self.subscriber)

    def on_emitToRoom(self, data):
        print "emitting to room: {} and myself".format(data['room'])
        self.emit('room_msg', data['msg'])
        self.emit_to_room(data['room'], 'room_msg', data['msg'])
