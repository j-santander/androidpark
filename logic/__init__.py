__author__ = 'julian'

from kivy.logger import Logger
import threading
import traceback

class L:
    COMPONENT="App"

    @staticmethod
    def info(s):
        try:
            Logger.info(L.__format(s))
        except:
            pass

    @staticmethod
    def debug(s):
        try:
            Logger.debug(L.__format(s))
        except:
            pass

    @staticmethod
    def error(s):
        try:
            Logger.error(L.__format(s))
        except:
            pass

    @staticmethod
    def __format(s):
        t=threading.current_thread()
        if type(s) is str:
            return L.COMPONENT+"_"+t.name+": "+s.decode('ascii','replace').encode('ascii','replace')
        if type(s) is unicode:
            return L.COMPONENT+"_"+t.name+": "+s.encode('ascii','replace')
        else:
            return L.COMPONENT+"_"+t.name+": "+str(s)
