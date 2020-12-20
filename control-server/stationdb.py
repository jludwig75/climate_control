#!/usr/bin/env python3
from datetime import datetime
import mariadb
import random
import time


_CREATE_STATION_SQL ="""
CREATE TABLE station (
        id INT NOT NULL PRIMARY KEY,
        ip_address VARCHAR(16) NOT NULL,
        host_name VARCHAR(64),
        location VARCHAR(255) )
"""

_CREATE_SENSOR_DATA_SQL = """
CREATE TABLE sensor_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        station_id INT NOT NULL,
        time TIMESTAMP NOT NULL,
        temperature FLOAT NOT NULL,
        humidity INT,
        INDEX(station_id),
        CONSTRAINT `fk_data_station`
            FOREIGN KEY (station_id) REFERENCES station (id)
            ON DELETE CASCADE
    )
"""

def _timeToTimeStamp(t):
    return datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')

class StationDatabase:
    @staticmethod
    def _createTables():
        conn = mariadb.connect(
                user='climate',
                password='Redhorn!1',
                host='localhost',
                database='climate'
            )

        with conn.cursor() as cursor:
            # Only for a destructive re-create
            # cursor.execute('DROP TABLE station')
            # cursor.execute('DROP TABLE sensor_data')

            cursor.execute('SHOW TABLES')
            tables = [row[0] for row in cursor]
            if not 'station' in tables:
                cursor.execute(_CREATE_STATION_SQL)
            if not 'sensor_data' in tables:
                cursor.execute(_CREATE_SENSOR_DATA_SQL)

    @staticmethod
    def createDabase():
        """ Create database and tables if they do not exist. Does nothing if they already exist """
        conn = mariadb.connect(
                user='climate',
                password='Redhorn!1',
                host='localhost'
            )

        with conn.cursor() as cursor:
            dbExists = False
            cursor.execute('SHOW DATABASES')
            for (database,) in cursor:
                if database == 'climate':
                    dbExists = True
                    break

            if not dbExists:
                cursor.execute('CREATE DATABASE climate')

        StationDatabase._createTables()

    def __init__(self):
        self._conn = mariadb.connect(
                user='climate',
                password='Redhorn!1',
                host='localhost',
                database='climate'
            )

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._conn.close()

    class Station:
        def __init__(self, conn, id, ipAddress, hostName, location):
            self._conn = conn
            self._id = id
            self._ipAddress = ipAddress
            self._hostName = hostName
            self._location = location

        @property
        def id(self):
            return self._id
        @property
        def ipAddress(self):
            return self._ipAddress
        @property
        def hostName(self):
            return self._hostName
        @property
        def location(self):
            return self._location

        def _rowToDataPoints(self, row):
            return { 'time': row[0], 'temperature': row[1], 'humidity': row[2]}

        @property
        def dataPoints(self):
            """ Station data points """
            cursor = self._conn.cursor()
            cursor.execute(f"SELECT time,temperature,humidity FROM sensor_data WHERE station_id={self._id}")
            return [self._rowToDataPoints(row) for row in cursor]
        
        def addDataPoint(self, dataPoint):
            """ Add datapoint for station """
            dataPoint['time'] = _timeToTimeStamp(dataPoint['time'])
            cursor = self._conn.cursor()
            cursor.execute(f"INSERT INTO sensor_data (station_id, time, temperature, humidity) VALUES ({self._id}, '{dataPoint['time']}', {dataPoint['temperature']}, {dataPoint['humidity']})")
            self._conn.commit()
        
        def clearDataPoints(self):
            """ Clear all station data points from database """
            cursor = self._conn.cursor()
            cursor.execute(f"DELETE FROM `sensor_data` WHERE station_id={self._id}")
            self._conn.commit()

        def remove(self):
            """ Remove station from registered station lists.
                Will fail if there are data points stored for this station.
                Remove them first by calling clearDataPoints.
            """
            cursor = self._conn.cursor()
            cursor.execute(f"DELETE FROM `station` WHERE id={self._id}")
            self._conn.commit()

    @property
    def stations(self):
        """ List registered stations """
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM station')
        return {row[0]: StationDatabase.Station(self._conn, *row) for row in cursor}
    
    def addStation(self, id, ipAddress, hostName=None, location=None):
        """ Add new station """
        cursor = self._conn.cursor()
        cursor.execute(f"INSERT INTO station (id, ip_address, host_name, location) VALUES ({id}, '{ipAddress}', '{hostName}', '{location}')")
        self._conn.commit()
        return StationDatabase.Station(self._conn, id, ipAddress, hostName, location)


def main():
    def testStationId(id):
        return int(1e6 + id)
    def virtualStationId(testId):
        assert testId >= 1e6
        return int(testId - 1e6)
    def isTestId(id):
        return int(id >= 1e6)

    def testCleanUp(db):
        # Clear out any previous test data
        for id, station in db.stations.items():
            if isTestId(id):
                station.clearDataPoints()
                station.remove()

    StationDatabase.createDabase()

    with StationDatabase() as db:
        testCleanUp(db)

        try:
            for station_id in range(3):
                stationId = testStationId(station_id)
                station = db.addStation(stationId, f'172.18.1.{65 + station_id}', f'tempstation0{station_id}', '')
                startTime = int(time.time())
                for i in range(50):
                    station.addDataPoint({ 'time': startTime + i, 'temperature': random.randint(69, 71), 'humidity': random.randint(38, 42) })
            for id, station in db.stations.items():
                if isTestId(id):
                    print(f'station {virtualStationId(station.id)}: ipAddress={station.ipAddress}, hostName={station.hostName}, location={station.location}')
                    for datapoint in station.dataPoints:
                        print(f"  {datapoint['time']}: temperature={datapoint['temperature']}, humidity={datapoint['humidity']}")
        finally:
            testCleanUp(db)

    print('End of test')

if __name__ == "__main__":
    main()