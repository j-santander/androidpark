from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from logic import L
import datetime
import calendar

from kivy.properties import ObjectProperty, StringProperty

from logic.daystatus import DayStatus
from ui.day import Day


class Month(BoxLayout):
    label = StringProperty()
    name = ObjectProperty()
    month = ObjectProperty()
    calendar = ObjectProperty()

    def update(self,state,pending):
        L.debug("pending operations: "+str(pending))
        for d in self.all_days:
            self.all_days[d].day=state[d]
            if pending is not None and d in pending:
                if pending[d]==DayStatus.TO_REQUEST and self.get_day(d).day.status==DayStatus.REQUESTED:
                    # Skip this case, server needs to keep track of it, but
                    # we don't
                    continue
                self.get_day(d).set()

    def init(self):
        L.debug("init of "+self.label)
        first_of_month=None
        if self.label == "current":
            today = datetime.date.today()
            first_of_month=datetime.date(today.year,today.month,1)
            self.name.text=first_of_month.strftime("%B")
        else:
            today = datetime.date.today()
            next_month=datetime.date(today.year,today.month,1)+datetime.timedelta(days=31)
            first_of_month=datetime.date(next_month.year,next_month.month,1)
            self.name.text=first_of_month.strftime("%B")

        # Add headers for the days of the week
        for w in DayStatus.WEEKDAYS:
            self.month.add_widget(Header(text=w,month=self))

        # Skip the cells up to the first day
        for i in range(0,first_of_month.weekday()):
            self.month.add_widget(Label())

        # Add the days of the month
        days_in_month=calendar.monthrange(first_of_month.year,first_of_month.month)[1]
        self.all_days={}
        for day in [first_of_month + datetime.timedelta(days=x) for x in range(0,days_in_month)]:
            d=Day(month=self)
            self.all_days[day]=d
            self.month.add_widget(d)

    def get_weekdays(self,weekday):
        return [w for day,w in self.all_days.iteritems() if day.weekday() == DayStatus.WEEKDAYS.index(weekday)]

    def get_monthdays(self):
        return [w for day,w in self.all_days.iteritems()]

    def get_day(self,day):
        if day in self.all_days:
            return self.all_days[day]
        else:
            return None

    def request_month(self):
        self.calendar.request_month(self)

    def request_weekday(self,weekday):
        self.calendar.request_weekday(self,weekday)

    def request_day(self,day):
        self.calendar.request_day(self,day)

    def unrequest_day(self,day):
        self.calendar.unrequest_day(self,day)


class Header(BoxLayout):
    text = StringProperty()
    month = ObjectProperty()
    def request_weekday(self):
        self.month.request_weekday(self.text)
