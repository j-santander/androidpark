# -*- encoding: utf-8 -*-
import threading

from Queue import Queue, Empty
from kivy.logger import Logger
from kivy.lib import osc
import pickle
import datetime
from time import sleep


class Ping:
    def __init__(self, calendar, config):
        self.calendar = calendar
        self.config = config

    def call(self, queue):
        queue.send_ping(self)

    def callback(self, msg):
        self.calendar.ping_back(True,msg['config'])

    def timedout(self):
        self.calendar.ping_back(False,None)


class Refresh:
    def __init__(self, calendar, config):
        self.calendar = calendar
        self.config = config

    def call(self, queue):
        queue.send_query(self)

    def callback(self, msg):
        Logger.debug("Got a response %s for %d" % (msg['response'], msg['id']))
        self.calendar.update_callback(msg['result'],msg['pending'],msg['status'])

    def timedout(self):
        self.calendar.update_callback(None, None,'Sin respuesta del servidor')


class Modify:
    def __init__(self, calendar, config, operations):
        self.calendar = calendar
        self.config = config
        self.operations = operations

    def call(self, queue):
        queue.send_modify(self)

    def callback(self, msg):
        Logger.debug("Got a response %s for %d" % (msg['response'], msg['id']))
        self.calendar.update_request()

    def timedout(self):
        pass


class QueryThread:
    def __init__(self, queue):
        self.queue = queue
        self.stopped = False
        self.thread = threading.Thread(name='query', target=self.run)
        osc.init()
        self.oscid = osc.listen(ipAddr='127.0.0.1', port=3334)
        osc.bind(self.oscid, self.handle_message, '/android_park')
        self.thread.start()
        self.pending = {}
        self.next_id = 0

    def run(self):
        while not self.stopped:
            try:
                # First check the osc
                if self.oscid is not None:
                    osc.readQueue(self.oscid)
                    event = self.queue.get(block=True, timeout=2)
                    event.call(self)
                    self.check_timeout()
                else:
                    sleep(.1)
            except Empty:
                self.check_timeout()

    def on_resume(self):
        self.oscid = osc.listen(ipAddr='127.0.0.1', port=3334)
        osc.bind(self.oscid, self.handle_message, '/android_park')
        self.pending = {}

    def on_pause(self):
        osc.dontListen(self.oscid)
        self.oscid = None
        self.pending = {}

    def on_stop(self):
        Logger.debug("on_stop()")
        osc.dontListen(self.oscid)
        self.oscid = None
        self.pending = {}
        self.stopped = True

    def handle_message(self, message, *args):
        pickle_msg = message[2]
        msg = pickle.loads(pickle_msg)

        if 'response' in msg:
            req = self.get_id(msg['id'])
            if req is not None:
                req.callback(msg)
            else:
                Logger.debug("Ignoring unknown response %d" % msg['id'])
        else:
            Logger.debug("Got a request %s for %d" % (msg['response'], msg['id']))

    def send_query(self, refresh):
        pickle_msg = pickle.dumps(
            {'request': 'query',
             'id': self.save_id(refresh),
             'config': refresh.config})
        osc.sendMsg('/android_park', [pickle_msg, ], port=3333)

    def send_ping(self, refresh):
        pickle_msg = pickle.dumps(
            {'request': 'ping',
             'id': self.save_id(refresh),
             'config': refresh.config})
        osc.sendMsg('/android_park', [pickle_msg, ], port=3333)

    def send_modify(self, modify):
        pickle_msg = pickle.dumps(
            {'request': 'modify',
             'id': self.save_id(modify),
             'config': modify.config,
             'operations': modify.operations})

        osc.sendMsg('/android_park', [pickle_msg, ], port=3333)

    def save_id(self, request):
        id = self.next_id
        self.pending[id] = request
        self.next_id += 1
        now = datetime.datetime.now()
        timeout = int(request.config.get('timers','timeout'))
        request.endtime = now + datetime.timedelta(seconds=timeout)
        request.id = id
        return id

    def get_id(self, id):
        if id in self.pending:
            req = self.pending[id]
            del self.pending[id]
            return req
        return None

    def check_timeout(self):
        now = datetime.datetime.now()
        timedout_id = [id for id in self.pending if self.pending[id].endtime < now]
        timedout = [self.get_id(id) for id in timedout_id]
        map(lambda (x): x.timedout(), timedout)
