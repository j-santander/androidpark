# Android Park
# Copyright (C) 2015  Julian Santander
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License v2 as published by
# the Free Software Foundation
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# -*- encoding: utf-8 -*-
import threading

from Queue import Queue, Empty
from logic import L
from kivy.lib import osc
from kivy.app import App

import pickle
import datetime
from time import sleep


class Request(object):
    def __init__(self):
        self.id=None
        self.endtime=None
        pass

    def call(self,queue):
        pass

    def callback(self, msg):
        pass

    def timedout(self):
        pass

    def get_timer(self):
        return int(App.get_running_app().config.get('timers','timeout'))


class Ping(Request):
    def __init__(self, calendar):
        super(Ping, self).__init__()
        self.calendar = calendar

    def call(self, queue):
        queue.send_ping(self)

    def callback(self, msg):
        self.calendar.ping_callback(True,msg['config'])

    def timedout(self):
        self.calendar.ping_callback(False,None)

    def get_timer(self):
        return 2


class Refresh(Request):
    def __init__(self, calendar):
        super(Refresh, self).__init__()
        self.calendar = calendar

    def call(self, queue):
        queue.send_refresh(self)

    def callback(self, msg):
        L.debug("Got a response %s for %d" % (msg['response'], msg['id']))
        self.calendar.refresh_callback(msg['result'],msg['pending'],msg['status'])

    def timedout(self):
        self.calendar.refresh_callback(None, None,'Sin respuesta del servidor')


class Modify(Request):
    def __init__(self, calendar, operations):
        super(Modify, self).__init__()
        self.calendar = calendar
        self.operations = operations

    def call(self, queue):
        queue.send_modify(self)

    def callback(self, msg):
        L.debug("Got a response %s for %d" % (msg['response'], msg['id']))
        self.calendar.modify_callback()

    def callback_partial(self,msg):
        L.debug("Got a partial response %s for %d" % (msg['response'], msg['id']))
        self.calendar.modify_partial_callback(msg['status'])


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
                    event = self.queue.get(block=True, timeout=1)
                    event.call(self)
                    self.check_timeout()
                    sleep(.1)
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
        L.debug("on_stop()")
        osc.dontListen(self.oscid)
        self.oscid = None
        self.pending = {}
        self.stopped = True

    def handle_message(self, message, *args):
        pickle_msg = message[2]
        msg = pickle.loads(pickle_msg)

        if 'response' in msg:
            if 'is_partial' in msg and msg['is_partial']:
                keep=True
            else:
                keep=False
            req = self.get_id(msg['id'],keep)
            if req is not None:
                if keep:
                    req.callback_partial(msg)
                else:
                    req.callback(msg)
            else:
                L.debug("Ignoring unknown response %d" % msg['id'])
        else:
            L.debug("Got a request %s for %d" % (msg['response'], msg['id']))

    def send_refresh(self, refresh):
        pickle_msg = pickle.dumps(
            {'request': 'query',
             'id': self.save_id(refresh),
             'config': self.get_config()})
        osc.sendMsg('/android_park', [pickle_msg, ], port=3333)

    def send_ping(self, refresh):
        pickle_msg = pickle.dumps(
            {'request': 'ping',
             'id': self.save_id(refresh),
             'config': self.get_config()})
        osc.sendMsg('/android_park', [pickle_msg, ], port=3333)

    def send_modify(self, modify):
        pickle_msg = pickle.dumps(
            {'request': 'modify',
             'id': self.save_id(modify),
             'config': self.get_config(),
             'operations': modify.operations})

        osc.sendMsg('/android_park', [pickle_msg, ], port=3333)

    def save_id(self, request):
        id = self.next_id
        self.pending[id] = request
        self.next_id += 1
        now = datetime.datetime.now()
        timeout = request.get_timer()
        request.endtime = now + datetime.timedelta(seconds=timeout)
        request.id = id
        return id

    def get_config(self):
        return App.get_running_app().config

    def get_id(self, id,keep=False):
        if id in self.pending:
            request = self.pending[id]
            if not keep:
                del self.pending[id]
            else:
                # refresh the timer.
                now = datetime.datetime.now()
                timeout = request.get_timer()
                request.endtime = now + datetime.timedelta(seconds=timeout)
            return request
        return None

    def check_timeout(self):
        now = datetime.datetime.now()
        timedout_id = [id for id in self.pending if self.pending[id].endtime < now]
        timedout = [self.get_id(id) for id in timedout_id]
        map(lambda (x): L.error("Time out on %d" % x.id),timedout)
        map(lambda (x): x.timedout(), timedout)
