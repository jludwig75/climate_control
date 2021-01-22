#!/usr/bin/env python3
from climate.topics import *
from datetime import datetime, timedelta
import mariadb
import random
import time

STATION_TABLE_NAME='station'
_CREATE_STATION_SQL = f"""
CREATE TABLE {STATION_TABLE_NAME} (
        id INT NOT NULL PRIMARY KEY,
        ip_address VARCHAR(16) NOT NULL,
        host_name VARCHAR(64),
        location VARCHAR(255) )
"""

SENSOR_DATA_TABLE_NAME='sensor_data'
_CREATE_SENSOR_DATA_SQL = f"""
CREATE TABLE {SENSOR_DATA_TABLE_NAME} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        station_id INT NOT NULL,
        time TIMESTAMP NOT NULL,
        temperature FLOAT NOT NULL,
        humidity INT,
        vcc FLOAT,
        INDEX(station_id),
        CONSTRAINT `fk_data_station`
            FOREIGN KEY (station_id) REFERENCES station (id)
            ON DELETE CASCADE
    )
"""

MODE_CHANGE_TABLE_NAME='mode_change'
_CREATE_TABLE_MODE_CHANGE_ = f"""
CREATE TABLE {MODE_CHANGE_TABLE_NAME} (
        day_of_week TINYINT NOT NULL,
        time_of_day INT NOT NULL,
        heat_set_point FLOAT,
        cool_set_point FLOAT,
        PRIMARY KEY(day_of_week, time_of_day)
    )
"""


def _timeToTimeStamp(t):
    if not isinstance(t, datetime):
        t = datetime.fromtimestamp(t)
    return t.strftime('%Y-%m-%d %H:%M:%S')

class StationDatabase:
    @staticmethod
    def _databaseName(useTestDatabase):
        if useTestDatabase:
            return 'climate_test'
        return 'climate'

    @staticmethod
    def _createTables(hostName, useTestDatabase):
        conn = mariadb.connect(
                user='climate',
                password='Redhorn!1',
                host=hostName,
                database=StationDatabase._databaseName(useTestDatabase)
            )

        with conn.cursor() as cursor:
            cursor.execute('SHOW TABLES')
            tables = [row[0] for row in cursor]
            if not STATION_TABLE_NAME in tables:
                cursor.execute(_CREATE_STATION_SQL)
            if not SENSOR_DATA_TABLE_NAME in tables:
                cursor.execute(_CREATE_SENSOR_DATA_SQL)
            if not MODE_CHANGE_TABLE_NAME in tables:
                cursor.execute(_CREATE_TABLE_MODE_CHANGE_)

    @staticmethod
    def createDabase(hostName='localhost', useTestDatabase=False):
        """ Create database and tables if they do not exist. Does nothing if they already exist """
        conn = mariadb.connect(
                user='climate',
                password='Redhorn!1',
                host=hostName
            )

        with conn.cursor() as cursor:
            dbExists = False
            cursor.execute('SHOW DATABASES')
            for (database,) in cursor:
                if database == StationDatabase._databaseName(useTestDatabase):
                    dbExists = True
                    break

            if not dbExists:
                cursor.execute(f'CREATE DATABASE {StationDatabase._databaseName(useTestDatabase)}')

        StationDatabase._createTables(hostName, useTestDatabase)
    
    @staticmethod
    def dropTestDatabase():
        conn = mariadb.connect(
                user='climate',
                password='Redhorn!1',
                host='localhost'
            )

        with conn.cursor() as cursor:
            cursor.execute(f'DROP DATABASE {StationDatabase._databaseName(useTestDatabase=True)}')

    def __init__(self, hostName='localhost', useTestDatabase=False):
        self._hostName = hostName
        self._conn = mariadb.connect(
                user='climate',
                password='Redhorn!1',
                host=self._hostName,
                database=StationDatabase._databaseName(useTestDatabase)
            )

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._conn.close()

    class Station:
        def __init__(self, conn, id, ipAddress, hostName, location, useTestDb=False):
            self._conn = conn
            self._id = id
            self._ipAddress = ipAddress
            self._hostName = hostName
            self._location = location
            self._useTestDb = useTestDb

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
            return { 'time': row[0], 'temperature': row[1], 'humidity': row[2], 'vcc': row[3]}

        def dataPoints(self, maxAgeSeconds=None, endTime=None):
            """ Station data points """
            cursor = self._conn.cursor()
            query = f"SELECT time,temperature,humidity,vcc FROM {SENSOR_DATA_TABLE_NAME} WHERE station_id={self._id}"
            end_time = time.time()
            if endTime is not None:
                end_time = float(endTime)
                query += f" AND time <= '{_timeToTimeStamp(end_time)}'"
            if maxAgeSeconds is not None:
                oldestTime = end_time - maxAgeSeconds
                query += f" AND time >= '{_timeToTimeStamp(oldestTime)}'"
            query += " ORDER BY time"
            cursor.execute(query)
            return [self._rowToDataPoints(row) for row in cursor]
        
        def addDataPoint(self, dataPoint):
            """ Add datapoint for station """
            dataPoint['time'] = _timeToTimeStamp(dataPoint['time'])
            cursor = self._conn.cursor()
            fieldList = 'station_id, time, temperature, humidity'
            values = [str(self._id), f"'{dataPoint['time']}'", str(dataPoint['temperature']), str(dataPoint['humidity'])]
            if dataPoint['vcc'] is not None:
                fieldList += ', vcc'
                values.append(str(dataPoint['vcc']))
            query = f"INSERT INTO {SENSOR_DATA_TABLE_NAME} ({fieldList}) VALUES ({','.join(values)})"
            cursor.execute(query)
            self._conn.commit()
        
        def clearDataPoints(self):
            """ Clear all station data points from database """
            cursor = self._conn.cursor()
            cursor.execute(f"DELETE FROM {SENSOR_DATA_TABLE_NAME} WHERE station_id={self._id}")
            self._conn.commit()

        def remove(self):
            """ Remove station from registered station lists.
                Will fail if there are data points stored for this station.
                Remove them first by calling clearDataPoints.
            """
            cursor = self._conn.cursor()
            cursor.execute(f"DELETE FROM {STATION_TABLE_NAME} WHERE id={self._id}")
            self._conn.commit()

    @property
    def stations(self):
        """ List registered stations """
        cursor = self._conn.cursor()
        cursor.execute(f'SELECT * FROM {STATION_TABLE_NAME}')
        return {row[0]: StationDatabase.Station(self._conn, *row) for row in cursor}
    
    def addStation(self, id, ipAddress, hostName=None, location=None):
        """ Add new station """
        cursor = self._conn.cursor()
        cursor.execute(f"INSERT INTO {STATION_TABLE_NAME} (id, ip_address, host_name, location) VALUES ({id}, '{ipAddress}', '{hostName}', '{location}')")
        self._conn.commit()
        return StationDatabase.Station(self._conn, id, ipAddress, hostName, location)

    class Schedule:
            def __init__(self, conn, modeChangeRows):
                self._conn = conn
                self._id = id
                self._schedule = [ [], [], [], [], [], [], [] ]
                for row in modeChangeRows:
                    dayOfWeek = int(row[0])
                    timeOfDay = int(row[1])
                    heatSetPoint = float(row[2]) if row[2] is not None else None
                    coolSetPoint = float(row[3]) if row[3] is not None else None
                    if dayOfWeek >= 7:
                        print(f'loaded invalid day of the week {dayOfWeek} from database schedule')
                        continue
                    if timeOfDay >= 60 * 60 * 24:
                        print(f'loaded invalid time of day {timeOfDay} from database schedule')
                        continue
                    modeChange = {'timeOfDay': timeOfDay}
                    if heatSetPoint is not None:
                        modeChange[HVAC_MODE_HEAT] = heatSetPoint
                    if coolSetPoint is not None:
                        modeChange[HVAC_MODE_COOL] = coolSetPoint
                    self._schedule[dayOfWeek].append(modeChange)

            def _decDayOfWeek(self, day):
                if day == 0:
                    return 6
                return day - 1
            
            def _getLastModeChangeBeforeToday(self, dayOfWeek):
                day = self._decDayOfWeek(dayOfWeek)
                while day != dayOfWeek:
                    if len(self._schedule[day]) > 0:
                        return self._schedule[day][-1]
                    day = self._decDayOfWeek(day)
                return None

            @property
            def currentMode(self):
                return self.getMode(datetime.now())
            
            def getMode(self, dt):
                timeOfDay = dt.second + (dt.minute + dt.hour * 60) * 60
                dayOfWeek = dt.weekday()
                todaysSchedule = self._schedule[dayOfWeek]
                currentMode = self._getLastModeChangeBeforeToday(dayOfWeek)
                for modeChange in todaysSchedule:
                    if timeOfDay >= modeChange['timeOfDay']:
                        currentMode = modeChange
                    else:
                        break
                return currentMode
            
            def addModeChange(self, dayOfWeek, timeOfDay, setPoints):
                assert dayOfWeek < 7 and timeOfDay < 60 * 60 * 24

                daysSchedule = self._schedule[dayOfWeek]
                for modeChange in daysSchedule:
                    if modeChange['timeOfDay'] == timeOfDay:
                        self.removeModeChange(dayOfWeek, timeOfDay)

                values = []
                values.append({'field': 'day_of_week', 'value': str(dayOfWeek)})
                values.append({'field': 'time_of_day', 'value': str(timeOfDay)})
                if HVAC_MODE_HEAT in setPoints:
                    values.append({'field': 'heat_set_point', 'value': str(setPoints[HVAC_MODE_HEAT])})
                if HVAC_MODE_COOL in setPoints:
                    values.append({'field': 'cool_set_point', 'value': str(setPoints[HVAC_MODE_COOL])})
                fieldString = ','.join([value['field'] for value in values])
                valueString = ','.join([value['value'] for value in values])
                query = f"INSERT INTO {MODE_CHANGE_TABLE_NAME} ({fieldString}) VALUES ({valueString})"
                cursor = self._conn.cursor()
                cursor.execute(query)
                self._conn.commit()
                modeChange = {'timeOfDay': timeOfDay}
                if HVAC_MODE_HEAT in setPoints:
                    modeChange[HVAC_MODE_HEAT] = setPoints[HVAC_MODE_HEAT]
                if HVAC_MODE_COOL in setPoints:
                    modeChange[HVAC_MODE_COOL] = setPoints[HVAC_MODE_COOL]
                self._schedule[dayOfWeek].append(modeChange)
                self._schedule[dayOfWeek].sort(key=lambda x: x['timeOfDay'])
            
            def removeModeChange(self, dayOfWeek, timeOfDay):
                assert dayOfWeek < 7 and timeOfDay < 60 * 60 * 24

                daysSchedule = self._schedule[dayOfWeek]
                for modeChange in daysSchedule:
                    if modeChange['timeOfDay'] == timeOfDay:
                        cursor = self._conn.cursor()
                        cursor.execute(f"DELETE FROM {MODE_CHANGE_TABLE_NAME} WHERE day_of_week={dayOfWeek} AND time_of_day={timeOfDay}")
                        self._conn.commit()
    
    @property
    def schedule(self):
        cursor = self._conn.cursor()
        cursor.execute(f'SELECT day_of_week, time_of_day, heat_set_point, cool_set_point FROM {MODE_CHANGE_TABLE_NAME} ORDER BY day_of_week, time_of_day')
        rows = [row for row in cursor]
        return StationDatabase.Schedule(self._conn, rows)

