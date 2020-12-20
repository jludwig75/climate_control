import cherrypy
import json
import random
from stationdb import StationDatabase
import time


class ReportServer(object):
    @cherrypy.expose
    def index(self):
        with open('html/index.html') as webPage:
            return webPage.read()

    @cherrypy.expose    # TODO: This will be replaced by a rest server, but we don't know what that looks like yet
    def sensorData(self):
        # map = { 0: [], 1: [], 2: [] }
        # startTime = int(time.time())
        # for key in map.keys():
        #     for i in range(60):
        #         map[key].append({ 'time': startTime + i * 60,
        #                           'temperature': random.randint(69,71),
        #                           'humidity': random.randint(38, 42)
        #                         })
        map = {}
        db = StationDatabase()
        for stationId, station in db.stations.items():
            map[stationId] = []
            for dataPoint in station.dataPoints:
                dataPoint['time'] = int(time.mktime(dataPoint['time'].timetuple()))
                if stationId == 1:  # Vent monitor
                    if dataPoint['temperature'] > 77:   # 5 degrees higher than the thermostat would ever be set to for heating
                        dataPoint['temperature'] = 77
                    elif dataPoint['temperature'] < 60: # 5 degrees lower than the thermostat would ever be set to for cooling
                        dataPoint['temperature'] = 60
                map[stationId].append(dataPoint)
        return json.dumps(map)
