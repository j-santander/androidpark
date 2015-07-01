from kivy.graphics import Color
import datetime

class DayStatus:
    """
    Contains a day requests
    """
    NOT_AVAILABLE = 0
    RESERVED = 1
    AVAILABLE = 2
    REQUESTED = 3
    BUSY = 4

    TO_FREE = 1
    TO_REQUEST = 2
    TO_UNREQUEST = 3

    COLOR_NOT_AVAILABLE= Color(153/255.,153/255.,153/255.,1)
    COLOR_RESERVED = Color(1,153/255.,0,1)
    COLOR_AVAILABLE = Color(51/255.,153/255.,0,1)
    COLOR_REQUESTED = Color(0,0,0,1)
    COLOR_BUSY= Color(1,0,0,1)

    WEEKDAYS=['L','M','X','J','V','S','D']

    def __init__(self, day, status, slot=None):
        self.day = day
        self.status = status
        self.slot = slot
        self.date = None

    def fix(self, ref):
        self.date = datetime.date(ref.year, ref.month, self.day)
        return self

    def __repr__(self):
        out = str(self.date) + " [" + DayStatus.status(self.status) + "]"
        if self.slot is not None:
            out += " (" + self.slot + ")"
        return out

    @staticmethod
    def status(s):
        if s == DayStatus.NOT_AVAILABLE:
            return "Not Avail"
        elif s == DayStatus.RESERVED:
            return "Reserved"
        elif s == DayStatus.AVAILABLE:
            return "Available"
        elif s == DayStatus.REQUESTED:
            return "Requested"
        elif s == DayStatus.BUSY:
            return "Busy"
        else:
            return "unknown"
