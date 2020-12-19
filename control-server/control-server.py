#!/usr/bin/env python3
import cherrypy
from reportserver import ReportServer
from stationdb import StationDatabase
import time


class Root(object):
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/report")

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    def report_sensor_data(self, station_id, temp, humidity):
        station_id = int(station_id)
        temp = int(temp)
        humidity = int(humidity)
        print(f'received sensor data: station={station_id}, temp={temp}, humidity={humidity}')
        db = StationDatabase()
        if station_id not in db.stations:
            station = db.addStation(int(station_id), cherrypy.request.remote.ip, cherrypy.request.remote.name)  # TODO get ip address and hostname. The location will be set later.
        else:
            station = db.stations[station_id]
        station.addDataPoint({ 'time': time.time(),
                                'temperature': temp,
                                'humidity': humidity
                                })

if __name__ == "__main__":
    conf = {
        '/': {

        }
    }

    cherrypy.config.update({'server.socket_port': 8080})
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.tree.mount(ReportServer(), '/report', conf)
    cherrypy.quickstart(Root(), '/', conf)
