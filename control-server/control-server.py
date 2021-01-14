#!/usr/bin/env python3
from climate.client import ClimateMqttClient, loadClientConfig
from climate.thermostatpolicy import AveragingThermostatPolicy
from climate.topics import *
import json


class ControlServer(ClimateMqttClient):
    def __init__(self, clientId, stationId, hvacStationId, ip, port, user, passwd):
        self._stationId = stationId
        self._hvacStationId = hvacStationId
        super().__init__(clientId,
                            CLIENT_HVAC_CONTROLLER,
                            ip,
                            port,
                            user,
                            passwd,
                            subscribedMessageMap={ CLIENT_HVAC_CONTROLLER: [HVAC_MSG_TYPE_REQUEST_MODE], CLIENT_STATION: [STATION_MSG_TYPE_SENSOR_DATA] })
        self._stationSensorMap = {}
        self._averageTemperature = 0
        self._policy = AveragingThermostatPolicy(0.5)   # 0.5 degree swing
        self._policy.setTargetTemperature(69)

    def run(self):
        self.connect(runForever=True)
    
    def _onMessage(self, stationId, messageType, message):
        if messageType == STATION_MSG_TYPE_SENSOR_DATA:
            try:
                senorData = json.loads(message.payload.decode('utf-8'))
            except Exception as e:
                print(f'Exception {e} parsing payload {message.payload}')
                return
            if not stationId in self._stationSensorMap:
                self._stationSensorMap[stationId] = {}
            self._stationSensorMap[stationId] = senorData
            self._computerAverageTemperature()
            print(f'Average temperature={self._averageTemperature:.2f}')
            desiredMode = self._policy.determineDesiredHvacMode(self._stationSensorMap)
            if desiredMode is not None:
                self._requestHvacMode(desiredMode)
    
    def _computerAverageTemperature(self):
        if len(self._stationSensorMap) == 0:
            return 0
        temp = 0
        count = 0
        for stationId, sensorData in self._stationSensorMap.items():
            temp += sensorData['temperature']
            count += 1
        self._averageTemperature = temp / count
    
    def _requestHvacMode(self, mode):
        print(f'Requesting HVAC controller mode {mode}')
        self.publish(self._hvacStationId, HVAC_MSG_TYPE_REQUEST_MODE, mode, qos=1, retain=True)

if __name__ == "__main__":
    cfg = loadClientConfig()
    hvacController = ControlServer('control-server-0', 0, 0, cfg['mqtt_broker'], cfg['mqtt_port'], cfg['mqtt_user_name'], cfg['mqtt_password'])
    hvacController.run()