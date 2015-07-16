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

from kivy.logger import Logger
import threading

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
