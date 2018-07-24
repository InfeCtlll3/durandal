import io
import sqlite3
import os.path
import glob
import os
import urllib.request
import ssl
from bs4 import BeautifulSoup
import lxml



class durandal:
    outputOptions = "db"
    dbfile = ""
    def __init__(self, logpath: str):
        if os.path.isdir(logpath):
            self.logpath = logpath
        else:
            raise Exception("you must configure a valid path in order to parse the logs.")
    def outputDB(self, *args):
        db = self.dbfile
        try:
            if not os.path.exists(r""+db):
                conn = sqlite3.connect(r"" + db)
                c = conn.cursor()
                c.execute("CREATE TABLE searchs (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, ipAddr TEXT, ipCountry TEXT, ipRegion TEXT, ipState TEXT, searchDate TEXT, searchHour TEXT, player TEXT, xforwarded TEXT, userAgent TEXT)")
            else:
                conn = sqlite3.connect(r"" + db)
                c = conn.cursor()
            c.execute("INSERT INTO searchs (ipAddr, ipCountry, ipRegion, ipState, searchDate, searchHour, player, xforwarded, userAgent) VALUES(?,?,?,?,?,?,?,?,?)", (args[0],args[1],args[2],args[3],args[4],args[5],args[6],args[7],args[8],))
        except Exception as e:
            print("exception happened in outputDB")
            print(str(e))
        finally:
            conn.commit()
            conn.close()
    def getFileLists(self) -> list:
        if os.name == "nt":
            char = "\\"
        else:
            char = "/"
        if self.logpath[-1:] is not char:
            self.logpath = self.logpath+char
        return glob.glob(self.logpath+"*access.log*")
    def parseFileLines(self, filename: str) -> list:
        try:
            _toreturn = []
            with open(filename) as fn:
                for line in fn:
                    _toreturn.append(line.rstrip('\n'))
            return _toreturn
        except Exception as e:
            print(str(e))
    def parseText(self, text):
        try:
            userAgent = text.split('" "')
            userAgent = userAgent[1].rstrip('"')
            text = text.split(" ")
            """
            text[0] == ip addr
            text[3] == date/hour
            text[5] == method (get or post)
            text[6] == page
            text[7] == http version
            text[8] == status code (200, 300, 404, etc)
            text[10] == xredirectfrom
            """
            _toreturn = [text[0], text[3].replace("[", ""), text[6], text[10], userAgent]
            """
            return 1 - ip
                   2 - date/hour
                   3 - page
                   4 - xredirect
                   5 - userAgent
            """
            return _toreturn
        except Exception as e:
            print(str(e))
    def getIpInfo(self, ip: str) -> list:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(
            "https://www.iplocation.net/search?cx=partner-pub-1026064395378929%3A2796854705&cof=FORID%3A10&ie=UTF-8&q={}".format(ip),
            context=context) as url:
            soup = BeautifulSoup(url.read(), 'lxml')
            toreturn = []
            for i in range(4):
                _str = str(soup.table.find_all("td")[i]).replace("<td>", "")
                _str = _str.replace("</td>", "")
                if i == 1:
                    _str = _str.split("<img")[0]
                toreturn.append(_str)
        """
        returns 0 - ip
                1 - Country
                2 - Region
                3 - City
        """
        return toreturn
    def splitDateAndHour(self, string: str) -> list:
        toreturn = []
        _str = ""
        string = string.split(":")
        for i in range(4):
            if i == 0:
                toreturn.append(string[i])
            if i < 3:
                _str = _str+string[i]+":"
        toreturn.append(_str)
        return toreturn
    def generateReport(self,  onlyMatch=""):
        files = durandal.getFileLists(self)
        for i in files:
            lines = durandal.parseFileLines(self, i)
            for j in lines:
                text = durandal.parseText(self, j)
                if onlyMatch is not "":
                    if onlyMatch in text[2]:
                        ip = text[0]
                        req = durandal.getIpInfo(self, ip)
                        country = req[1]
                        region = req[2]
                        city = req[3]
                        date = durandal.splitDateAndHour(self, text[1])[0]
                        hour = durandal.splitDateAndHour(self, text[1])[1]
                        player = text[2].replace(onlyMatch, "")
                        redirect = text[3]
                        useragent = text[4]

                        durandal.outputDB(self, ip, country, region, city, date, hour, player, redirect, useragent)
