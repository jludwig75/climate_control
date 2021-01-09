#!/usr/bin/env python3
from climate.client import ClimateMqttClient, loadClientConfig
from climate.topics import *
import sys
import time
from test.esp8266 import ESP, millis, delay
from test.ota import ota_setup, ota_onLoop



report_interval_ms = 60 * 1000


class MockStationClient(ClimateMqttClient):
    def __init__(self, stationId, ip, port, user, passwd):
        super().__init__(f'dummy-station-{stationId}',
                            CLIENT_STATION,
                            ip,
                            port,
                            user,
                            passwd,
                            subscribedMessageMap={ CLIENT_STATION: [STATION_MSG_TYPE_WAIT_FOR_UPDATE] },
                            subscriptionClientId=stationId)
        self._stationId = stationId
        self._waitForUpdate = False

    def _onMessage(self, stationId, messageType, message):
        assert stationId == self._stationId

        # print(f'Received message: retain={message.retain} timestamp={message.timestamp} topic="{message.topic}" payload="{message.payload}"')
        try:
            payloadData = message.payload.decode('utf-8')
        except Exception as e:
            print(f'Exception parsing message payload {message.payload}: {e}')
            return
        print(f'Received data from station {stationId}: {messageType} => {payloadData}')
        self._waitForUpdate = True if payloadData.lower() == 'yes' else False

    @property
    def waitForUpdate(self):
        return self._waitForUpdate

    UPDATE_STATE_NOT_WAITING = 'NotWaiting'
    UPDATE_STATE_WAITING = 'Waiting'
    UPDATE_STATE_UPDATING = 'Updating'
    UPDATE_STATE_UPDATE_COMPLETE = 'UpdateComplete'
    def sendUpdateState(self, state):
        print(f'Station {self._stationId} sending update state "{state}"')
        self.publish(self._stationId, STATION_MSG_TYPE_UPDATE_STATE, state, qos=1, retain=True)


class UpdateChecker:
    def __init__(self, mqttClient):
        self._lastUpdateCheck = 0
        self._otaInitialized = False
        self._updating = False
        self._mqttClient = mqttClient
    def checkForUpdate(self):
        t = millis()
        if self._lastUpdateCheck == 0 or t - self._lastUpdateCheck > 30 * 1000:
            self._lastUpdateCheck = t
            if not self._updating and not self._mqttClient.waitForUpdate:
                self._mqttClient.sendUpdateState(MockStationClient.UPDATE_STATE_NOT_WAITING)
                print("Disconnecting mqtt client...")
                self._mqttClient.disconnect()
                return False
            if not self._otaInitialized:
                print('Initializing OTA code')
                ota_setup(self._onOtaStart, self._onOtaEnd)
                self._mqttClient.sendUpdateState(MockStationClient.UPDATE_STATE_WAITING)
                self._otaInitialized = True

        if self._otaInitialized:
            ota_onLoop()
        return True
    
    def _onOtaStart(self):
        self._updating = True
        self._mqttClient.sendUpdateState(MockStationClient.UPDATE_STATE_UPDATING)
    
    def _onOtaEnd(self):
        self._mqttClient.sendUpdateState(MockStationClient.UPDATE_STATE_UPDATE_COMPLETE)
        self._mqttClient.disconnect()
        self._updating = False


class StationSketch:
    def __init__(self, id):
        self._id = id

    def setup(self):
        cfg = loadClientConfig()
        print('Running sketch...')
        self._mqttClient = MockStationClient(self._id, cfg['mqtt_broker'], cfg['mqtt_port'], cfg['mqtt_user_name'], cfg['mqtt_password'])
        self._update = UpdateChecker(self._mqttClient)
        self._mqttClient.connect()
        print('Waiting for MQTT...')
        delay(1000) # Give MQTT a chance to connect
        print('End setup')

    def loop(self):
        if not self._update.checkForUpdate():
            print('Sleeping...')
            ESP.deepSleep(report_interval_ms * 1000)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Invlid command arguments expect <station_id>')
        stationId = 11
    else:
        stationId = int(sys.argv[1])
    print(f'Simulating station {stationId}...')
    stationSketch = StationSketch(stationId)
    ESP.runSketch(stationSketch)