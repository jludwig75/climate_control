#!/usr/bin/env python3
import cherrypy


class Root(object):
    @cherrypy.expose
    def index(self):
        print('connection received')

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    def report_sensor_data(self, station_id, temp, humidity):
        print(f'received sensor data: station={station_id}, temp={temp}, humidity={humidity}')


if __name__ == "__main__":
    conf = {
        '/': {

        }
    }

    cherrypy.config.update({'server.socket_port': 8080})
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.quickstart(Root(), '/', conf)
