# -*- encoding: utf-8 -*-
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from time import sleep
from kivy.logger import Logger
from kivy.lib import osc
from logic.server import ServerInterface,ServerException
from logic.daystatus import DayStatus
import datetime
import pytz

import pickle



class ServerThread:
    def __init__(self):
        Logger.debug("Service is running")
        osc.init()
        self.oscid = osc.listen(ipAddr='127.0.0.1', port=3333)
        osc.bind(self.oscid, self.handle_message, '/android_park')
        self.server = None
        self.pending = {}
        self.last_time = None
        self.config = None
        self.met=pytz.timezone('Europe/Madrid')
        self.t1=datetime.time(hour=0,minute=0,second=0,tzinfo=self.met) # 00:00
        self.t2=datetime.time(hour=15,minute=0,second=0,tzinfo=self.met) # 15:00
        self.t3=datetime.time(hour=17,minute=30,second=0,tzinfo=self.met) # 17:30
        self.t4=datetime.time(hour=23,minute=59,second=59,tzinfo=self.met) # 23:59

    def handle_message(self, message, *args):
        pickle_msg = message[2]
        msg = pickle.loads(pickle_msg)
        if self.server is None:
            self.server = ServerInterface()

        self.config = msg['config']
        self.server.config(self.config)

        if msg['request'] == 'ping':
            self.ping(msg['id'])
        if msg['request'] == 'query':
            self.query(msg['id'])
        if msg['request'] == 'modify':
            self.pending=msg['operations']
            self.modify(msg['id'])

    def run(self):
        while True:
            osc.readQueue(self.oscid)
            if len(self.pending) > 0:
                # Pending operations
                if self.check_interval():
                    self.modify(-1)
            sleep(.1)

    def ping(self,id):
        self.send_ping_result(id)

    def query(self,id):
        Logger.debug("Calling query id:%s " % id)
        try:
            result=self.server.query()
            self.update_pending(result)
            self.send_query_result(id,result,self.pending)
        except ServerException as e:
            self.send_query_result(id,None,self.pending,e.status)

    def modify(self,id):
        Logger.debug("Calling modify id:%s " % id)
        try:
            result=self.server.modify(self.pending)
            self.last_time = datetime.datetime.now(tz=self.met)
            self.update_pending(result)
            self.send_modify_result(id,"OK")
        except ServerException as e:
            self.send_modify_result(id,e.status)


    def send_modify_result(self, id, status=None):
        Logger.debug("Send modify result %d" % id)
        pickle_msg = pickle.dumps({
            'response': 'modify',
            'id': id,
            'status': status})
        osc.sendMsg('/android_park', [pickle_msg, ], port=3334)


    def send_query_result(self, id, result, pending,status=None):
        Logger.debug("Send query result %d" % id)
        pickle_msg = pickle.dumps({
            'response': 'query',
            'id': id,
            'result': result,
            'pending': pending,
            'status': status})
        osc.sendMsg('/android_park', [pickle_msg, ], port=3334)

    def send_ping_result(self, id):
        Logger.debug("Send ping result %d" % id)
        pickle_msg = pickle.dumps({
            'response': 'ping',
            'id': id,
            'config': self.config})
        osc.sendMsg('/android_park', [pickle_msg, ], port=3334)

    def check_interval(self):
        '''
        Check if it is time for a new attempt
        :return: True if it is time for a new attempt
        '''
        now=datetime.datetime.now(tz=self.met)
        tomorrow = now.date() + datetime.timedelta(days=1)
        f1 = int(self.config.get("timers","frequency"))*60
        f2 = int(self.config.get("timers","frequency2"))*60
        if (self.t1 <= now.time() < self.t2) or (self.t3 <= now.time() < self.t4):
            # Period 00:00 - 14:59: attempt every 30 min
            if self.last_time is None or (now - self.last_time).total_seconds() > f1:
                return True
        if (self.t2 <= now.time() < self.t3) and tomorrow in self.pending:
            # Period 15:00 - 17:30: attempt 1 min (but only if there's something pending for tomorrow
            if self.last_time is None or (now - self.last_time).total_seconds() > f2:
                return True
        return False

    def update_pending(self,result):
        '''
        Update the pending operations with the result retrieved from the web.
        :param result:
        :return: None
        '''
        to_delete=[]

        Logger.debug("pending (before) "+str(self.pending))
        for i in sorted(self.pending):
            today = datetime.datetime.now(tz=self.met)
            if (i.month - today.month) not in (0, 1):
                Logger.error(str(i) + " is neither current nor next month")
                to_delete.append(i)
                continue
            if self.pending[i]==DayStatus.TO_FREE:
                # Request was to Free... target should be Free.
                if i not in result or result[i].status in (DayStatus.AVAILABLE,DayStatus.NOT_AVAILABLE):
                    to_delete.append(i)

            if self.pending[i]==DayStatus.TO_REQUEST:
                # Request was to Request.... target is Assigned.
                if i not in result or result[i].status in (DayStatus.RESERVED,DayStatus.NOT_AVAILABLE):
                    to_delete.append(i)

            if self.pending[i]==DayStatus.TO_UNREQUEST:
                # Request was to Unrequest.
                if i not in result or result[i].status in (DayStatus.AVAILABLE,DayStatus.NOT_AVAILABLE):
                    to_delete.append(i)

        for i in to_delete:
            del self.pending[i]

        Logger.debug("pending (after) "+str(self.pending))

if __name__ == '__main__':
    print(__file__)
    ServerThread().run()
