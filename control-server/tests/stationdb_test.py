#!/usr/bin/env python3
from climate.stationdb import StationDatabase
from climate.topics import *
from datetime import datetime, timedelta
import random
import time
import unittest


def timeOfDayToSeconds(hour, minute, second = 0):
    return 60 * (60 * hour + minute) + second


class StationDbTest(unittest.TestCase):
    def setUp(self):
        StationDatabase.createDabase(useTestDatabase=True)
        self.db = StationDatabase(useTestDatabase=True)

    def tearDown(self):
        self.db.close()
        StationDatabase.dropTestDatabase()

    def testStationsAndSensorData(self):
        dataPoints = {}
        for station_id in range(3):
            dataPoints[station_id] = []
            station = self.db.addStation(station_id, f'172.18.1.{65 + station_id}', f'tempstation0{station_id}', '')
            startTime = int(time.time())
            for i in range(50):
                dataPoint = { 'time': startTime + i, 'temperature': random.randint(69, 71), 'humidity': random.randint(38, 42), 'vcc': random.randint(300, 340) / 100.0}
                dataPoints[station_id].append(dataPoint)
                station.addDataPoint(dataPoint.copy())
            for dataPoint in dataPoints[station_id]:
                dataPoint['time'] = datetime.fromtimestamp(dataPoint['time'])
        for id, station in self.db.stations.items():
            station_id = station.id
            stationDataPoints = station.dataPoints()
            testDataPoints = dataPoints[station_id]
            self.assertEqual(len(stationDataPoints), len(testDataPoints))
            for i in range(len(stationDataPoints)):
                self.assertEqual(stationDataPoints[i], testDataPoints[i])
                dataPoint = stationDataPoints[i]

    def testSchedule(self):
        schedule = self.db.schedule

        # Clear out any existing schedule
        for dayOfWeek in range(len(schedule._schedule)):
            for modeChange in schedule._schedule[dayOfWeek]:
                schedule.removeModeChange(dayOfWeek, modeChange['timeOfDay'])
            schedule._schedule[dayOfWeek].clear()

        for dayOfWeek in range(7):
            schedule.addModeChange(dayOfWeek, timeOfDayToSeconds(7, 0), { HVAC_MODE_HEAT: 69, HVAC_MODE_COOL: 70 })
            schedule.addModeChange(dayOfWeek, timeOfDayToSeconds(8, 0), { HVAC_MODE_HEAT: 71, HVAC_MODE_COOL: 72 })
            schedule.addModeChange(dayOfWeek, timeOfDayToSeconds(21, 0), { HVAC_MODE_HEAT: 70, HVAC_MODE_COOL: 71 })
            schedule.addModeChange(dayOfWeek, timeOfDayToSeconds(22, 0), { HVAC_MODE_HEAT: 67, HVAC_MODE_COOL: 68 })

        for dayOfWeek in range(7):
            dt = datetime(2021, 1, 4 + dayOfWeek)
            tt = dt + timedelta(seconds=timeOfDayToSeconds(6, 59))
            mode = schedule.getMode(tt)
            self.assertTrue(HVAC_MODE_HEAT in mode)
            self.assertTrue(mode[HVAC_MODE_HEAT] == 67)
            tt = dt + timedelta(seconds=timeOfDayToSeconds(7, 00))
            mode = schedule.getMode(tt)
            self.assertTrue(HVAC_MODE_HEAT in mode)
            self.assertEqual(mode[HVAC_MODE_HEAT], 69)

if __name__ == '__main__':
    unittest.main()
