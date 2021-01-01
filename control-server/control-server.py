#!/usr/bin/env python3
import cherrypy
import os
from stationdb import StationDatabase
import time


class Root(object):
    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    def report_sensor_data(self, station_id, temp, humidity, vcc=None):
        station_id = int(station_id)
        temp = float(temp)
        humidity = int(humidity)
        if vcc is not None:
            vcc = float(vcc)
        else:
            vcc = 0
        print(f'received sensor data: station={station_id}, temp={temp}, humidity={humidity}, vcc={vcc}')
        with StationDatabase() as db:
            if station_id not in db.stations:
                station = db.addStation(int(station_id), cherrypy.request.remote.ip, cherrypy.request.remote.name)  # TODO get ip address and hostname. The location will be set later.
            else:
                station = db.stations[station_id]
            station.addDataPoint({ 'time': time.time(),
                                    'temperature': temp,
                                    'humidity': humidity,
                                    'vcc': vcc
                                    })

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET'])
    def wait_for_update(self):
        return 'no'

if __name__ == "__main__":
    cherrypy.config.update({'server.socket_port': 8080})
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.quickstart(Root(), '/')
