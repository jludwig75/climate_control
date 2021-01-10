from climate.topics import *


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

    def setTargetTemperature(self, targetTemperature):
        self._targetTemperature = targetTemperature

    def determineDesiredHvacMode(self, stationSensorMap):
        averageStationTemperature = self._averageTemperature(stationSensorMap)
        if averageStationTemperature < self._targetTemperature - self._swing:
            return HVAC_MODE_HEAT
        if averageStationTemperature > self._targetTemperature + self._swing:
            return HVAC_MODE_COOL
        return HVAC_MODE_FAN
    
    def _averageTemperature(self, stationSensorMap):
        if len(stationSensorMap.keys()) == 0:
            return None
        temp = 0
        for stationId, sensorState in stationSensorMap.items():
            temp += sensorState['temperature']
        return temp / len(stationSensorMap.keys())
