#!/usr/bin/env python3
import cherrypy
import os
from stationdb import StationDatabase
import time


class Root(object):
    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET'])
    def wait_for_update(self):
        return 'no'

if __name__ == "__main__":
    cherrypy.config.update({'server.socket_port': 8080})
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.quickstart(Root(), '/')
