# -*- encoding: utf-8 -*-
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.app import App

from kivy.properties import ObjectProperty, StringProperty

from logic.daystatus import DayStatus
import datetime


class Querying(ModalView):
    pass

class Confirm(ModalView):
    ok_button = ObjectProperty()
    cancel_button = ObjectProperty()
    text = StringProperty()
    def cancel(self):
        self.dismiss()
        self.on_accept=None
    def accept(self):
        self.dismiss()
        if self.on_accept is not None:
            self.on_accept()
        self.on_accept=None

class Error(ModalView):
    ok_button = ObjectProperty()
    text = StringProperty()
    def cancel(self):
        self.dismiss()
        self.on_accept=None
    def accept(self):
        self.dismiss()

class Calendar(FloatLayout):
    current_month = ObjectProperty()
    next_month = ObjectProperty()
    querying = ObjectProperty()
    confirm = ObjectProperty()
    error = ObjectProperty()
    toggle_service = ObjectProperty()
    service_running = ObjectProperty()
    last_update = ObjectProperty()

    def on_service_running(self,instance, value):
        if value:
            self.toggle_service.img_stop.opacity = 1
            self.toggle_service.img_play.opacity = 0
        else:
            self.toggle_service.img_stop.opacity = 0
            self.toggle_service.img_play.opacity = 1


    def open_settings(self):
        self.app.open_settings()

    def toggle_service_state(self):
        if self.service_running:
            self.service_running = False
            self.app.stop_service()
        else:
            self.service_running = True
            self.app.start_service()

    def update_request(self):
        if not self.service_running:
            self.error.text="El Servicio en segundo plano no está corriendo"
            self.error.open()
            return

        Logger.debug("Update start")
        self.last_update = datetime.datetime.now()
        self.querying.open()
        self.app.do_refresh(self)

    def update(self, state,pending,status=None):
        if not state:
            Logger.error("state is None")
            self.querying.dismiss()
            if status is not None:
                self.error.text=status
            else:
                self.error.text="Error desconocido"
            self.error.open()
            return

        self.unrequest_month(self.current_month)
        self.unrequest_month(self.next_month)
        self.current_month.update(state,pending)
        self.next_month.update(state,pending)
        Logger.debug("Update ends")
        self.querying.dismiss()

    def update_callback(self, state, pending, status=None):
        if status is not None:
            Logger.debug("Update status: " + str(status)+" pending operations: "+str(pending))

        Clock.schedule_once(lambda (dt): self.update(state,pending,status))

    def timer_callback(self, dt):
        now = datetime.datetime.now()
        self.ping_request()

        if not self.is_config_ready():
            self.open_settings()

        refresh=int(self.app.config.get("timers","data_refresh"))*60

        if self.service_running and self.is_config_ready() and \
               (self.last_update is None or (now - self.last_update).total_seconds() > refresh):
            self.update_request()

    def ping_request(self):
        self.app.do_ping(self)

    def is_config_ready(self):
        return (self.app.config.get('credentials','username') != "") and (self.app.config.get('credentials','password') != "")

    def ping_back(self,value,config):
        if self.service_running != value:
            Logger.debug("Service state change: "+str(value))
        self.service_running = value

    def send(self):
        if not self.service_running:
            self.error.text="El Servicio en segundo plano no está corriendo"
            self.error.open()
            return

        Logger.debug("Send start")
        days = self.get_days_with_change()
        operations = {}
        for d in days:
            if d.day.status != DayStatus.RESERVED and d.day.status != DayStatus.REQUESTED:
                # request
                operations[d.day.date] = DayStatus.TO_REQUEST
            elif d.day.status == DayStatus.RESERVED:
                # free
                operations[d.day.date] = DayStatus.TO_FREE
            elif d.day.status == DayStatus.REQUESTED:
                # unrequest
                operations[d.day.date] = DayStatus.TO_UNREQUEST
        free_count = len([x for x in operations if operations[x] == 1])
        unrequest_count = len([x for x in operations if operations[x] == 3])
        request_count = len([x for x in operations if operations[x] == 2])
        self.confirm.text = "Se liberarán %d plazas, se quitará la solicitud para %d plazas y se solicitarán %d nuevas plazas" \
                            % (free_count, unrequest_count, request_count)
        self.confirm.on_accept=lambda: self.app.do_send(self, operations)
        self.confirm.open()

    def init(self):
        self.querying = Querying()
        self.querying.dismiss()
        self.confirm = Confirm()
        self.confirm.dismiss()
        self.current_month.init()
        self.next_month.init()
        self.error = Error()
        self.error.dismiss()
        self.last_update = None
        self.app=App.get_running_app()
        # do the first update
        Clock.schedule_once(self.timer_callback, 1)
        # ... and then do every 5 s
        Clock.schedule_interval(self.timer_callback, 5)

    def request_month(self, month):
        map(lambda x: x.set_request_only(), month.get_monthdays())

    def unrequest_month(self, month):
        map(lambda x: x.reset(), month.get_monthdays())

    def request_weekday(self, month, weekday):
        map(lambda x: x.set_request_only(), month.get_weekdays(weekday))

    def request_day(self, month, day):
        month.get_day(day.date).set()

    def unrequest_day(self, month, day):
        month.get_day(day.date).reset()

    def get_days_with_change(self):
        return filter(lambda x: x.needs_change(),
                      self.current_month.get_monthdays() +
                      self.next_month.get_monthdays())
