from climate.topics import *
import json
import os


STATION_WEIGHTS_FILE_NAME='station_weights.json'    # TODO: This needs to be moved to the database. Issue #3

def loadStationWeights():
    if not os.path.exists(STATION_WEIGHTS_FILE_NAME):
        return {}
    with open(STATION_WEIGHTS_FILE_NAME) as f:
        return json.loads(f.read())


class ThermostatPolicy:
    def setTargetTemperature(self, targetTemperature):
        assert False # implement in derived class

    """ Can return None when no request should be made """
    def determineDesiredHvacMode(self, stationSensorMap):
        assert False # implement in derived class

class AveragingThermostatPolicy(ThermostatPolicy):
    def __init__(self, swing):
        self._targetTemperature = 70
        self._swing = swing
        self._stationWeights = loadStationWeights()

    def setTargetTemperature(self, targetTemperature):
        self._targetTemperature = targetTemperature

    def determineDesiredHvacMode(self, stationSensorMap):
        averageStationTemperature = self._averageTemperature(stationSensorMap)
        if averageStationTemperature < self._targetTemperature - self._swing:
            return HVAC_MODE_HEAT
        if averageStationTemperature > self._targetTemperature + self._swing:
            return HVAC_MODE_COOL
        return HVAC_MODE_FAN
    
    def _getStationWeight(self, stationId):
        if stationId in self._stationWeights:
            return self._stationWeights[stationId]
        return 1

    def _averageTemperature(self, stationSensorMap):
        if len(stationSensorMap.keys()) == 0:
            return None
        temp = 0
        count = 0
        for stationId, sensorState in stationSensorMap.items():
            weight = self._getStationWeight(stationId)
            temp += weight * sensorState['temperature']
            count += weight
        return temp / count
