#!/usr/bin/env python3
from climate.stationdb import StationDatabase
from climate.topics import *
from datetime import datetime, timedelta
import random
import time

def timeOfDayToSeconds(hour, minute, second = 0):
    return 60 * (60 * hour + minute) + second


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

    def testStationsAndSensorData(db):
        for station_id in range(3):
            stationId = testStationId(station_id)
            station = db.addStation(stationId, f'172.18.1.{65 + station_id}', f'tempstation0{station_id}', '')
            startTime = int(time.time())
            for i in range(50):
                station.addDataPoint({ 'time': startTime + i, 'temperature': random.randint(69, 71), 'humidity': random.randint(38, 42), 'vcc': random.randint(300, 340) / 100.0})
        for id, station in db.stations.items():
            if isTestId(id):
                print(f'station {virtualStationId(station.id)}: ipAddress={station.ipAddress}, hostName={station.hostName}, location={station.location}')
                for datapoint in station.dataPoints():
                    print(f"  {datapoint['time']}: temperature={datapoint['temperature']}, humidity={datapoint['humidity']}, vcc={datapoint['vcc']}")

    def testSchedule(db):
        schedule = db.schedule

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
            print(dt, dt.weekday())
            tt = dt + timedelta(seconds=timeOfDayToSeconds(6, 59))
            mode = schedule.getMode(tt)
            print(mode)
            assert HVAC_MODE_HEAT in mode
            assert mode[HVAC_MODE_HEAT] == 67
            tt = dt + timedelta(seconds=timeOfDayToSeconds(7, 00))
            mode = schedule.getMode(tt)
            print(mode)
            assert HVAC_MODE_HEAT in mode
            assert mode[HVAC_MODE_HEAT] == 69


    StationDatabase.createDabase()

    with StationDatabase() as db:
        testCleanUp(db)

        try:
            testStationsAndSensorData(db)
        finally:
            testCleanUp(db)

        try:
            testSchedule(db)
        finally:
            testCleanUp(db)

    print('End of test')

if __name__ == "__main__":
    main()