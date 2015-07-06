__version__ = '0.1'
import kivy

kivy.require('1.0.5')

from kivy.app import App

from ui.settings import SettingPassword

from logic.query_thread import QueryThread,Refresh,Modify,Ping
from Queue import Queue
from kivy.utils import platform
from kivy.logger import Logger


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

    def do_send(self,calendar,operations):
        self.queue.put(Modify(calendar,operations))

    def build_config(self,config):
        #config.setdefaults('credentials',
        #    {'username' : "PA0013282",
        #     'password' : "w7gYg3DT"})
        config.setdefaults('credentials',
            {'username' : "",
             'password' : ""})
        config.setdefaults('network',{'host': "79.148.237.226"})
        config.setdefaults('timers',
                           {'data_refresh': 5,
                           'frequency': 120,
                           'frequency2': 5,
                           'timeout': 15})

    def start_service(self):
        if self.service is not None:
            return
        Logger.info("Trying to start service")
        if platform == 'android':
            from android import AndroidService
            service = AndroidService('android park service', 'running')
            service.start('service started')
            self.service = service


    def stop_service(self):
        if self.service is None:
            return
        Logger.info("Trying to stop service")
        if platform == 'android':
            from android import AndroidService
            self.service.stop()
            self.service=None

    def build_settings(self, settings):
        settings.register_type("password",SettingPassword)
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
              "title": "Host",
              "desc": "Web del parking",
              "section": "network",
              "key": "host"
            },
            { "type": "numeric",
              "title": "Refresco de datos",
              "desc": "Tiempo en minutos entre consultas al servidor para refrescar los datos",
              "section": "timers",
              "key": "data_refresh"
            },
            { "type": "numeric",
              "title": "Reintentos",
              "desc": "Tiempo en minutos entre reintentos de peticiones al servidor (00:00-14:59/17:30-23:59)",
              "section": "timers",
              "key": "frequency"
            },
            { "type": "numeric",
              "title": "Reintentos en la repesca",
              "desc": "Tiempo en minutos entre reintentos de peticiones al servidor (15:00-17:30)",
              "section": "timers",
              "key": "frequency2"
            },
            { "type": "numeric",
              "title": "Temporizador de Servicio",
              "desc": "Timeout en segundos de la comunicacion App y Service",
              "section": "timers",
              "key": "timeout"
            }
        ]
        """
        settings.add_json_panel('Android Park',self.config, data=jsondata)

    def on_config_change(self, config, section, key, value):
        self.root.update_request()


if __name__ == '__main__':
    CalendarApp().run()

