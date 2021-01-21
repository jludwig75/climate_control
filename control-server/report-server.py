#!/usr/bin/env python3
import cherrypy
import functools
import json
import os
from stationdb import StationDatabase
import time


def smoothData(data, period, get, put):
    lastValues = []
    for d in data:
        lastValues.append(get(d))
        if len(lastValues) > period:
            lastValues.pop(0)
        put(d, sum(lastValues) / len(lastValues))

def differentiateData(data, getValue, getTime, createNewItem):
    dData = [createNewItem(data[0], 0)]
    lastDp = None
    for dp in data:
        if lastDp != None:
            if getTime(dp) == getTime(lastDp):
                continue
            newValue = (getValue(dp) - getValue(lastDp)) / (getTime(dp) - getTime(lastDp))
            if abs(newValue) < 0.004:
                newValue = 0
            dData.append(createNewItem(dp, newValue))
        lastDp = dp
    return dData


class ReportServer(object):
    @cherrypy.expose
    def index(self):
        with open('html/index.html') as webPage:
            return webPage.read()

    @cherrypy.expose    # TODO: This will be replaced by a rest server, but we don't know what that looks like yet
    def sensorData(self, maxAgeSeconds=None, endTime=None):
        if maxAgeSeconds is not None:
            maxAgeSeconds = float(maxAgeSeconds)
        if endTime is not None:
            endTime = float(endTime)
        map = {}
        with StationDatabase() as db:
            stations = db.stations
            for stationId, station in stations.items():
                map[stationId] = []
                for dataPoint in station.dataPoints(maxAgeSeconds=maxAgeSeconds, endTime=endTime):
                    dataPoint['time'] = int(time.mktime(dataPoint['time'].timetuple()))
                    map[stationId].append(dataPoint)

            dataPoints = stations[1].dataPoints(maxAgeSeconds=maxAgeSeconds, endTime=endTime).copy()
            if len(dataPoints) >= 10:
                maxValue = max(dataPoint['temperature'] for dataPoint in dataPoints)
                minValue = min(dataPoint['temperature'] for dataPoint in dataPoints)

                map[100] = self._calculateThermostatState(stations[1], maxValue, minValue, maxAgeSeconds, endTime)
        
        return json.dumps(map)

    def _calculateThermostatState(self, ventMonitorData, onValue, offValue, maxAgeSeconds, endTime):
        # TODO: This might need some addition debouncing/filtering. Only time will tell how accurate it is.
        def getItem(item):
            return item['temperature']
        def putItem(item, value):
            item['temperature'] = value
        def createNewItem(oldItem, value):
            item = oldItem.copy()
            item['temperature'] = value
            return item
        data = ventMonitorData.dataPoints(maxAgeSeconds=maxAgeSeconds, endTime=endTime).copy()

        for dataPoint in data:
            dataPoint['time'] = int(time.mktime(dataPoint['time'].timetuple()))

        # 1. Smooth the data
        smoothData(data, 3, lambda item: item['temperature'], putItem)

        # 2. Differentiate the data
        dData = differentiateData(data, lambda item: item['temperature'], lambda item: item['time'], createNewItem)

        # 3. Analyze the differentiated data
        lastDp = None
        lastThermostatValue = None
        thermostatState = []
        for dp in dData:
            if lastDp is not None:
                lastTemp = getItem(lastDp)
                currentTemp = getItem(dp)
                if lastTemp <= 0 and currentTemp > 0:
                    if lastThermostatValue == offValue:
                        thermostatState.append({'time': lastDp['time'], 'temperature': offValue})
                    thermostatState.append({'time': lastDp['time'], 'temperature': onValue})
                    lastThermostatValue = onValue
                elif lastTemp >= 0 and currentTemp < 0:
                    if lastThermostatValue == onValue:
                        thermostatState.append({'time': lastDp['time'], 'temperature': onValue})
                    thermostatState.append({'time': lastDp['time'], 'temperature': offValue})
                    lastThermostatValue = offValue
            lastDp = dp
        return thermostatState

if __name__ == "__main__":
    conf = {
        '/': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.abspath('./html')
        }
    }

    cherrypy.config.update({'server.socket_port': 8081})
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.quickstart(ReportServer(), '/', conf)
