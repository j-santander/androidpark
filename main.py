# -*- encoding: utf-8 -*-
__version__ = '0.2'
import kivy

kivy.require('1.0.5')

from kivy.app import App

from ui.settings import SettingPassword,SettingBoundedNumeric

from logic.query_thread import QueryThread,Refresh,Modify,Ping
from Queue import Queue
from kivy.utils import platform
from logic import L


class CalendarApp(App):
    def on_start(self):
        self.service=None
        self.queue=Queue()
        self.query_thread=QueryThread(self.queue)
        self.start_service()
        self.root.init()

    def on_stop(self):
        self.query_thread.on_stop()

    def on_pause(self):
        self.query_thread.on_pause()
        return True

    def on_resume(self):
        self.query_thread.on_resume()
        return True

    def do_refresh(self,calendar):
        self.queue.put(Refresh(calendar))

    def do_ping(self,calendar):
        self.queue.put(Ping(calendar))

    def do_modify(self,calendar,operations):
        self.queue.put(Modify(calendar,operations))

    def build_config(self,config):
        #config.setdefaults('credentials',
        #    {'username' : "PA0013282",
        #     'password' : "w7gYg3DT"})
        config.setdefaults('credentials',
            {'username' : "",
             'password' : ""})
        config.setdefaults('network',{'host': "79.148.237.226"})
        config.setdefaults('general',{'pattern':""})
        config.setdefaults('timers',
                           {'data_refresh': 5,
                           'frequency': 120,
                           'frequency2': 5,
                           'timeout': 15})

    def start_service(self):
        if self.service is not None:
            return
        L.info("Trying to start service")
        if platform == 'android':
            from android import AndroidService
            service = AndroidService('AndroidPark(ing)', 'en ejecución...')
            service.start('service started')
            self.service = service


    def stop_service(self):
        if self.service is None:
            return
        L.info("Trying to stop service")
        if platform == 'android':
            from android import AndroidService
            self.service.stop()
            self.service=None

    def build_settings(self, settings):
        settings.register_type("password",SettingPassword)
        settings.register_type("bounded_numeric",SettingBoundedNumeric)
        jsondata = """
        [
            { "type": "title",
              "title": "Android Park" },
            { "type": "string",
              "title": "Nombre de Usuario",
              "desc": "Nombre de usuario en la web del parking",
              "section": "credentials",
              "key": "username"
            },
            { "type": "password",
              "title": "Password",
              "desc": "Password para la web del parking",
              "section": "credentials",
              "key": "password"
            },
            { "type": "string",
              "title": "Patrón automático",
              "desc": "Patrón (e.g. L,M,X,J,V) que se aplicará cuando se abre un mes",
              "section": "general",
              "key": "pattern"
            },
            { "type": "string",
              "title": "Host",
              "desc": "Web del parking",
              "section": "network",
              "key": "host"
            },
            { "type": "bounded_numeric",
              "min": 0,
              "max": 1440,
              "title": "Refresco de datos",
              "desc": "Tiempo en minutos entre consultas al servidor para refrescar los datos [0-1440], 0 significa que no se refrescará",
              "section": "timers",
              "key": "data_refresh"
            },
            { "type": "bounded_numeric",
              "title": "Reintentos",
              "min": 0,
              "max": 1440,
              "desc": "Tiempo en minutos entre reintentos de peticiones al servidor (00:00-14:59/17:30-23:59) [0-1440], 0 significa que no se reintentará",
              "section": "timers",
              "key": "frequency"
            },
            { "type": "bounded_numeric",
              "title": "Reintentos en la repesca",
              "min": 0,
              "max": 1440,
              "desc": "Tiempo en minutos entre reintentos de peticiones al servidor (15:00-17:30) [0-1440], 0 significa que no se reintentará",
              "section": "timers",
              "key": "frequency2"
            },
            { "type": "bounded_numeric",
              "title": "Temporizador de Servicio",
              "min": 1,
              "max": 60,
              "desc": "Timeout en segundos de la comunicacion App y Service [1-60]",
              "section": "timers",
              "key": "timeout"
            }
        ]
        """
        settings.add_json_panel('Android Park',self.config, data=jsondata)

    def on_config_change(self, config, section, key, value):
        self.root.refresh_request()


if __name__ == '__main__':
    CalendarApp().run()

