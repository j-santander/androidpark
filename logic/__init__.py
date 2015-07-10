__author__ = 'julian'

from kivy.logger import Logger
import threading

class L:
    COMPONENT="App"

    @staticmethod
    def info(s):
        Logger.info(L.__format(s))

    @staticmethod
    def debug(s):
        Logger.debug(L.__format(s))

    @staticmethod
    def error(s):
        Logger.error(L.__format(s))

    @staticmethod
    def __format(s):
        t=threading.current_thread()
        return L.COMPONENT+"_"+t.name+"/"+str(t.ident)+": "+s.encode('ascii','replace')