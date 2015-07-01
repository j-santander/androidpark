# -*- encoding: utf-8 -*-
from logic.daystatus import DayStatus
from kivy.logger import Logger

import requests
import datetime
import bs4
import pytz

class ServerException(Exception):
    def __init__(self, status):
        self.status = status

class ServerInterface:
    def __init__(self):
        self.session = None
        self.met = pytz.timezone('Europe/Madrid')


    def config(self,appconfig):
        self.host = appconfig.get('network','host')
        self.username = appconfig.get('credentials','username')
        self.password = appconfig.get('credentials','password')

    def login(self):
        Logger.debug("Starting login")
        #
        # Start a session so that we can reuse cookies
        #
        self.session = requests.Session()

        #
        # Prepare the login request
        #
        try:
            r = self.session.post("http://" + self.host + "/index.php", data={
                "usuario": self.username,
                "contrasena": self.password,
                "aceptar": "ACEPTAR"})

            if r.status_code != requests.codes.ok:
                status = "Fallo al hacer login " + self.host + ", respuesta:" + r
                raise ServerException(status)

        except (KeyboardInterrupt, requests.ConnectionError) as e:
            status = str(e)
            raise ServerException(status)
        #
        # Parse the web page we have read
        #
        Logger.debug("Parsing query result")

        state=self.parse_months(r.text)

        if state is None:
            raise ServerException("Problema consultando con el servidor, es probable que el usuario/contraseña sean incorrectos")
        return state

    def query(self):
        Logger.debug("Starting query")

        state=None

        if self.session is None:
            #
            # No session, start a login session
            # the result is fine as a query result
            #
            state = self.login()
            return state

        #
        # Reuse session
        #
        try:
            r = self.session.get("http://" + self.host + "/perfil.php")
            if r.status_code != requests.codes.ok:
                status = "Error consultando al " + self.host + ", respuesta:" + r
                raise ServerException(status)
            #
            # Parse the web page we have read
            #
            Logger.debug("Parsing query result")
            state = self.parse_months(r.text)

            if state is None:
                Logger.debug("parsing failed, login might have failed")
                self.session = None
                return self.query()

        except (KeyboardInterrupt, requests.ConnectionError, ServerException) as e:
            status = str(e)
            Logger.error(status)
            # try to login again
            self.session = None
            return self.query()

        return state

    def modify(self, operations):
        if self.session is None:
            self.login()

        last_text=""

        for i in sorted(operations):
            today = datetime.datetime.now(tz=self.met)
            if (i.month - today.month) not in (0, 1):
                Logger.error(str(i) + " is neither current nor next month")
                continue
            try:
                Logger.debug("Requesting " + str(i) + ": " + self.map_operation(operations[i]))
                r = self.session.post("http://" + self.host + "/perfil.php", data={
                    "dia": i.day,
                    "mes": i.month - today.month,
                    "libre": operations[i],
                })

                if r.status_code != requests.codes.ok:
                    Logger.debug("Failed request on " + self.host + ", response:" + r)
                    continue

                # Parse the web page to obtain the result message
                Logger.debug(self.parse_result(r.text))
                last_text=r.text
            except (KeyboardInterrupt, requests.ConnectionError) as e:
                Logger.debug("Petición falló en " + self.host + ", con:\n" + str(e))

        return self.parse_months(last_text)


    def map_operation(self, o):
        """
        Returns a string representation of an operation code
        :param o:
        :return:
        """
        operations = {
            DayStatus.TO_FREE: "Free",
            DayStatus.TO_REQUEST: "Request",
            DayStatus.TO_UNREQUEST: "Unrequest",
        }
        if o in operations:
            return operations[o]
        else:
            return "Unknown"

    def unique_list(self, seq):
        """
        Returns a list with the unique
        values of the input sequence
        :param seq:
        :return: the list with the unique values.
        """
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    def get_table(self, t):
        while t.name != "table":
            t = t.parent
        return t

    def parse_result(self,text):
        soup = bs4.BeautifulSoup(text, "html5lib")
        spans = soup.select("span")
        for s in spans:
            if "red" in s.attrs['style']:
                return s.string

        return "unknown"

    def parse_months(self, text):
        """
        Parse the web page to obtain the
        list of the days and their status
        :param text: the text from the http response
        :return: a dictionary with the status of the days
        """
        result = []
        out = {}

        soup = bs4.BeautifulSoup(text, "html5lib")
        # get the cells... this is better reference I could get
        toptables = soup.select("body > table ")

        if len(toptables) != 6:
            return out

        tables = [toptables[4].tbody.tr.td.table, toptables[5].tbody.find_all('tr')[1].td.table]

        # Now, for each table.
        for t in tables:
            month = []
            # for each week (row)
            for w in t.select("tr"):
                # for each day (cell)
                for d in w.select("td"):
                    # only pay attention to colored cells
                    if "bgcolor" in d.attrs:
                        # Try to parse the cell
                        cell_list = d.select("div")
                        if len(cell_list) == 0:
                            # No divs... not interested in this
                            continue
                        elif len(cell_list) < 2:
                            # only one div
                            day = cell_list[0]
                            slot = None
                        else:
                            # two divs.
                            (day, slot) = cell_list

                        # some days appear with two nested divs.
                        if day.string is not None:
                            mday = int(day.string.strip())
                        else:
                            mday = int([x for x in day.stripped_strings][0])
                        rslot = None
                        # parse the status based on the color
                        if d.attrs['bgcolor'] == '#999999':
                            status = DayStatus.NOT_AVAILABLE
                        elif d.attrs['bgcolor'] == '#FF9900':
                            status = DayStatus.RESERVED
                            if slot is not None:
                                rslot = [x for x in slot.stripped_strings][0]
                        elif d.attrs['bgcolor'] == '#339900':
                            status = DayStatus.AVAILABLE
                        elif d.attrs['bgcolor'] == '#000000':
                            status = DayStatus.REQUESTED
                        else:
                            status = DayStatus.BUSY
                        month.append(DayStatus(mday, status, rslot))
            result.append(month)

        if len(result) != 2:
            return out
        # Now rebuild the date
        today = datetime.datetime.now(tz=self.met)
        today = datetime.date(today.year, today.month, 1)
        for d in [x.fix(today) for x in result[0]]:
            out[d.date] = d
        for d in [x.fix(today + datetime.timedelta(days=31)) for x in result[1]]:
            out[d.date] = d
        return out
