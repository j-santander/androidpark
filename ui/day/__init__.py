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

from kivy.graphics import Color, Line, Rectangle
from kivy.graphics import StencilPush, StencilPop, StencilUse
from kivy.uix.boxlayout import BoxLayout

from kivy.properties import ObjectProperty

from logic.daystatus import DayStatus


class Day(BoxLayout):
    month = ObjectProperty()
    day_button = ObjectProperty()
    day = ObjectProperty()
    clipping = ObjectProperty(allownone=True)
    band = ObjectProperty(allownone=True)

    def redraw(self):
        if self.band is not None:
            self.clipping.pos = self.pos
            self.clipping.size = self.size
            self.band.points = (self.x, self.y + self.height * 2 / 3,
                                self.x + self.width * 1 / 3, self.y + self.height)
            self.band.width = self._calculate_band_width()

    def toggle(self):
        if self.day is not None:
            if self.band is None:
                self.request()
            else:
                self.unrequest()

    def request(self):
        if self.day is not None:
            if self.band is None:
                self.month.request_day(self.day)

    def unrequest(self):
        if self.day is not None:
            if self.band is not None:
                self.month.unrequest_day(self.day)

    def set_request_only(self):
        if self.day is not None:
            if self.band is None:
                if self.day.status == DayStatus.AVAILABLE:
                    self.add_band(DayStatus.COLOR_RESERVED)
                elif self.day.status == DayStatus.BUSY:
                    self.add_band(DayStatus.COLOR_RESERVED)
                else:
                    pass

    def set(self):
        if self.day is not None:
            if self.band is None:
                if self.day.status == DayStatus.RESERVED:
                    self.add_band(DayStatus.COLOR_AVAILABLE)
                elif self.day.status == DayStatus.REQUESTED:
                    self.add_band(DayStatus.COLOR_AVAILABLE)
                elif self.day.status == DayStatus.AVAILABLE:
                    self.add_band(DayStatus.COLOR_RESERVED)
                elif self.day.status == DayStatus.BUSY:
                    self.add_band(DayStatus.COLOR_RESERVED)
                else:
                    pass

    def reset(self):
        if self.day is not None:
            if self.band is not None:
                self.remove_band()

    def add_band(self, color):
        with self.canvas:
            StencilPush()
            self.clipping = Rectangle(pos=self.pos, size=self.size)
            StencilUse()
            Color(rgba=color.rgba)
            self.band = Line(points=(self.x, self.y + self.height * 2. / 3,
                                     self.x + self.width * 1. / 3, self.y + self.height),
                             width=self._calculate_band_width())
            StencilPop()

    def _calculate_band_width(self):
        w = min([self.width, self.height]) * 1. / 12
        if w < 2:
            return 2
        else:
            return w

    def remove_band(self):
        self.canvas.remove(self.band)
        self.band = None
        self.clipping = None

    def needs_change(self):
        return self.band is not None

    def on_day(self, instance, value):
        if value is not None:
            self.day_button.text = str(value.date.day)
            if value.status == DayStatus.NOT_AVAILABLE:
                self.day_button.background_color = DayStatus.COLOR_NOT_AVAILABLE.rgba
                self.disabled = True
            elif value.status == DayStatus.RESERVED:
                self.day_button.background_color = DayStatus.COLOR_RESERVED.rgba
                self.day_button.text += "\n" + value.slot
            elif value.status == DayStatus.AVAILABLE:
                self.day_button.background_color = DayStatus.COLOR_AVAILABLE.rgba
            elif value.status == DayStatus.REQUESTED:
                self.day_button.background_color = DayStatus.COLOR_REQUESTED.rgba
            elif value.status == DayStatus.BUSY:
                self.day_button.background_color = DayStatus.COLOR_BUSY.rgba
            else:
                pass
        else:
            self.day_button.text = ''
