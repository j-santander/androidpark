__author__ = 'julian'

from kivy.logger import Logger
import threading

class L:
    COMPONENT="App"
    @staticmethod
    def debug(s):
        t=threading.current_thread()
        Logger.debug(L.COMPONENT+"_"+t.name+"/"+str(t.ident)+": "+str(s))

    @staticmethod
    def error(s):
        t=threading.current_thread()
        Logger.error(L.COMPONENT+"_"+t.name+"/"+str(t.ident)+": "+str(s))