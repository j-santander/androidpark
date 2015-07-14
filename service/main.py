# -*- encoding: utf-8 -*-
import os, sys, random

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from time import sleep
from logic import L
from kivy.lib import osc
from kivy.utils import platform
from logic.server import ServerInterface,ServerException
from logic.daystatus import DayStatus
from Queue import Queue, Empty

import datetime
import pytz
import threading
import traceback

import pickle

if platform == 'android':
    from jnius import autoclass
    Class = autoclass('java.lang.Class')
    NotificationBuilder = autoclass('android.app.Notification$Builder')
    PythonService = autoclass('org.renpy.android.PythonService')
    PythonActivity = autoclass('org.renpy.android.PythonActivity')
    PendingIntent = autoclass('android.app.PendingIntent')
    Intent = autoclass('android.content.Intent')
    Context = autoclass('android.content.Context')

class ServerThread:
    def __init__(self):
        L.debug("Service is running")
        # Initialize internal queue
        self.thread = threading.Thread(name='execution', target=self.async_run)
        self.internal_queue = Queue()
        self.thread.start()
        # Initialize OSC
        osc.init()
        self.oscid = osc.listen(ipAddr='127.0.0.1', port=3333)
        osc.bind(self.oscid, self.handle_message, '/android_park')
        self.server = None
        self.pending = {}
        self.last_time = None
        self.notified = True
        self.config = None
        # Initialize timezones
        self.met=pytz.timezone('Europe/Madrid')
        self.t1=datetime.time(hour=0,minute=0,second=0,tzinfo=self.met) # 00:00
        self.t2=datetime.time(hour=15,minute=0,second=0,tzinfo=self.met) # 15:00
        self.t3=datetime.time(hour=17,minute=30,second=0,tzinfo=self.met) # 17:30
        self.t4=datetime.time(hour=23,minute=59,second=59,tzinfo=self.met) # 23:59

    def async_run(self):
        while True:
            try:
                event = self.internal_queue.get(block=True, timeout=1)
                event()
            except Empty:
                pass
            except Exception as e:
                L.error("Exception:\n"+traceback.format_exc())

    def handle_message(self, message, *args):
        pickle_msg = message[2]
        msg = pickle.loads(pickle_msg)
        L.debug("Received message %s" % msg['request'])

        if self.server is None:
            self.server = ServerInterface()

        self.config = msg['config']
        self.server.config(self.config)

        if msg['request'] == 'ping':
            # Reply immediatelly to pings.
            self.ping(msg['id'])
        if msg['request'] == 'query':
            self.internal_queue.put(lambda: self.query(msg['id']))
        if msg['request'] == 'modify':
            self.pending=msg['operations']
            self.internal_queue.put(lambda: self.modify(msg['id']))

        L.debug("End Received message %s" % msg['request'])

    def run(self):
        while True:
            osc.readQueue(self.oscid)
            if not self.notified:
                self.update_notification("Intento: "+self.last_time.strftime('%Y-%m-%d %H:%M'))
                self.notified=True
            if len(self.pending) > 0:
                # Pending operations
                if self.check_pattern():
                    self.add_pattern()
                if self.check_interval():
                    self.modify(-1)
            sleep(.1)

    def ping(self,id):
        self.send_ping_result(id)

    def query(self,id):
        L.debug("Calling query id: %s " % id)
        try:
            result=self.server.query()
            self.update_pending(result)
            self.send_query_result(id,result,self.pending)
        except ServerException as e:
            self.send_query_result(id,None,self.pending,e.status)

    def modify(self,id):
        L.debug("Calling modify id:%s " % id)
        try:
            result=self.server.modify(self.pending,lambda (s):self.send_modify_partial_result(id,s))
            self.last_time = datetime.datetime.now(tz=self.met)
            self.notified = False
            self.update_pending(result)
            self.send_modify_result(id,"OK")
        except ServerException as e:
            self.send_modify_result(id,e.status)

    def send_modify_result(self, id, status=None):
        L.debug("Send modify result %d" % id)
        pickle_msg = pickle.dumps({
            'response': 'modify',
            'id': id,
            'status': status})
        osc.sendMsg('/android_park', [pickle_msg, ], port=3334)

    def send_modify_partial_result(self,id,status):
        L.debug("Send modify partial result %d" % id)
        pickle_msg = pickle.dumps({
            'response': 'modify',
            'is_partial': True,
            'id': id,
            'status': status})
        osc.sendMsg('/android_park', [pickle_msg, ], port=3334)

    def send_query_result(self, id, result, pending,status=None):
        L.debug("Send query result %d" % id)
        pickle_msg = pickle.dumps({
            'response': 'query',
            'id': id,
            'result': result,
            'pending': pending,
            'status': status})
        osc.sendMsg('/android_park', [pickle_msg, ], port=3334)

    def send_ping_result(self, id):
        L.debug("Send ping result %d" % id)
        pickle_msg = pickle.dumps({
            'response': 'ping',
            'id': id,
            'config': self.config})
        osc.sendMsg('/android_park', [pickle_msg, ], port=3334)

    def check_pattern(self):
        random.seed()
        now=datetime.datetime.now(tz=self.met)
        pattern = self.config.get("general","pattern")
        next_month=(now.month+1)
        if next_month==13:
            next_month=1
        pending_for_next_month=[i for i in self.pending if i.month==next_month]
        random_minute=random.randrange(0,60)
        if pattern != "" and now.day == 1 and now.hour > 11 and now.minute > random_minute and len(pending_for_next_month)==0:
            # Add the pattern the first day of the month, at the 11:XXam, and
            # only if there's nothing pending for next month.
            return True
        else:
            return False

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
            if f1>0 and (self.last_time is None or (now - self.last_time).total_seconds() > f1):
                return True
        if (self.t2 <= now.time() < self.t3) and tomorrow in self.pending:
            # Period 15:00 - 17:30: attempt 1 min (but only if there's something pending for tomorrow
            if f2>0 and (self.last_time is None or (now - self.last_time).total_seconds() > f2):
                return True
        if now.hour == 14 and now.minute > 50 and now.second > random.randange(0,60) \
            and (now - self.last_time).total_seconds > (10*60):
            # One final at 14:50 + random seconds
            # and only if we haven't requested  more than 10 minutes ago.
            return True
        return False

    def add_pattern(self):
        pattern = self.config.get("general","pattern")
        dates_from_pattern = [t[1] for t in self.parse_spec(pattern) if t[0]]
        L.debug("Using pattern %s, adding " % (pattern,str(dates_from_pattern)))
        self.pending.update({ t:DayStatus.TO_REQUEST for t in dates_from_pattern})
        if len(dates_from_pattern)>0:
            self.modify(-1)

    def parse_spec(self,text):
        # This is going to be a comma separated list of tokens:
        # - token: <weekday>|<date>
        # - neg: !<token>
        # - all: all=L,M,X,J,V
        # - weekday: <raw>
        # - raw: L,M,X,J,V (L=cL,nL)
        # - current: c<raw>
        # - next: n<raw>
        # - date: [[YYYY-]MM-]DD

        specs = text.split(',')
        result = []
        for s in specs:
            tk = self.parse_token(s)
            if tk is not None:
                result.extend(tk)
        return result

    def parse_token(self,s):
        # Parse individual tokens.
        s = s.strip()
        if len(s) == 0:
            return None
        if s == "all":
            return self.parse_spec("L,M,X,J,V")
        if s in ("L", "M", "X", "J", "V"):
            today = datetime.datetime.today()
            if today.month==12:
                next_month = datetime.date(today.year+1, 1, 1)
            else:
                next_month = datetime.date(today.year, today.month+1, 1)
            out = []
            for i in range(1, 32):
                try:
                    d = datetime.date(next_month.year, next_month.month, i)
                    if (s[1] == "L" and d.weekday() == 0) or \
                            (s[1] == "M" and d.weekday() == 1) or \
                            (s[1] == "X" and d.weekday() == 2) or \
                            (s[1] == "J" and d.weekday() == 3) or \
                            (s[1] == "V" and d.weekday() == 4):
                        out.append((True, d))
                except:
                    pass
            return out
        if s[0] == '!':
            tkns = self.parse_token(s[1:])
            return [(not tk[0], tk[1]) for tk in tkns]


    def update_pending(self,result):
        '''
        Update the pending operations with the result retrieved from the web.
        :param result:
        :return: None
        '''
        to_delete=[]

        L.info("pending (before) "+str(self.pending))
        for i in sorted(self.pending):
            today = datetime.datetime.now(tz=self.met)
            if (i.month - today.month) not in (0, 1):
                L.error(str(i) + " is neither current nor next month")
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

        for i in [i for i in result if result[i].status == DayStatus.REQUESTED ]:
            self.pending[i]=DayStatus.TO_REQUEST

        L.info("pending (after) "+str(self.pending))

    def update_notification(self,text):
        L.info("Notification: "+text)
        if platform == 'android':
            try:
                service = PythonService.mService
                builder = NotificationBuilder(service)
                builder.setSmallIcon(service.getApplicationInfo().icon)
                builder.setContentTitle("AndroidPark(ing)")
                builder.setContentText(text)
                contextIntent = Intent(service, Class.forName('org.renpy.android.PythonActivity'))
                pIntent = PendingIntent.getActivity(service, 0, contextIntent,PendingIntent.FLAG_UPDATE_CURRENT)
                builder.setContentIntent(pIntent)
                manager = service.getSystemService(Context.NOTIFICATION_SERVICE)
                manager.notify(1,builder.build())
            except:
                L.error("Exception:\n"+traceback.format_exc())


if __name__ == '__main__':
    L.COMPONENT="Service"
    ServerThread().run()
