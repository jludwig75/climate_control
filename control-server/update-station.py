#!/usr/bin/env python3
from climate.client import ClimateMqttClient, loadClientConfig
from climate.topics import *
import sys
import threading
import time


class UpdateControlClient(ClimateMqttClient):
    def __init__(self, clientId, ip, port, user, passwd):
        super().__init__(clientId, CLIENT_STATION, ip, port, user, passwd, subscribedMessageTypes=[STATION_MSG_TYPE_UPDATE_STATE])
        self._waitForUpdate = False
        self._stationStates = {}
        self._stationStateChangeCallbacks = {}

    def registerStateChangeCallback(self, stationId, callback):
        self._stationStateChangeCallbacks[stationId] = callback

    def _onMessage(self, stationId, messageType, message):
        payloadData = message.payload.decode('utf-8')
        # print(f'Received data from station {stationId}: {messageType} => {payloadData}')

        if stationId not in self._stationStates:
            self._stationStates[stationId] = UpdateControlClient.UPDATE_STATE_UNKNWON

        if payloadData in [UpdateControlClient.UPDATE_STATE_NOT_WAITING, UpdateControlClient.UPDATE_STATE_WAITING, UpdateControlClient.UPDATE_STATE_UPDATING, UpdateControlClient.UPDATE_STATE_UPDATE_COMPLETE]:
            self._stationStates[stationId] = payloadData
        else:
            self._stationStates[stationId] = UpdateControlClient.UPDATE_STATE_INVALID
        # print(f'Station {stationId} update state: {self._stationStates[stationId]}')
        if stationId in self._stationStateChangeCallbacks:
            self._stationStateChangeCallbacks[stationId](self._stationStates[stationId])

    UPDATE_STATE_UNKNWON = 'Uknown'
    UPDATE_STATE_NOT_WAITING = 'NotWaiting'
    UPDATE_STATE_WAITING = 'Waiting'
    UPDATE_STATE_UPDATING = 'Updating'
    UPDATE_STATE_UPDATE_COMPLETE = 'UpdateComplete'
    UPDATE_STATE_INVALID = 'INVALID'
    def stationUpdateState(self, stationId):
        if stationId not in self._stationStates:
            self._stationStates[stationId] = UpdateControlClient.UPDATE_STATE_UNKNWON
        return self._stationStates[stationId]

    def requestUpdate(self, stationId):
        self.publish(stationId, STATION_MSG_TYPE_WAIT_FOR_UPDATE, 'yes', qos=1, retain=True)
    
    def releaseFromUpdate(self, stationId):
        self.publish(stationId, STATION_MSG_TYPE_WAIT_FOR_UPDATE, 'no', qos=1, retain=True)



class StationUpdater:
    WAITING_FOR_WAITING_FOR_UPDATE = "WaitingForWaitForUpdate"
    WAITING_FOR_UPDATE_TO_START = "WaitingForUpdateStart"
    WAITING_FOR_UPDATE_TO_COMPLETE = "WaitingForUpdateComplete"
    WAITING_FOR_REBOOT = "WaitingForReboot"
    COMPLETE = "Complete"
    def __init__(self, stationId, mqttClient):
        self._mqttClient = mqttClient
        self._stationId = stationId
        self._state = StationUpdater.WAITING_FOR_WAITING_FOR_UPDATE
    def update(self):
        try:
            self._mqttClient.registerStateChangeCallback(self._stationId, self._onUpdateStateChange)
            self._mqttClient.requestUpdate(self._stationId)
            print(f'Waiting for station {self._stationId} to prepare for update...')
            while self._state != StationUpdater.COMPLETE:
                time.sleep(1)
        finally:
            self._mqttClient.releaseFromUpdate(self._stationId)
    def _onUpdateStateChange(self, state):
        # print(f'on-state-change[{self._stationId}]: StationState:[{state}] UpdaterState:[{self._state}]')
        if self._state == StationUpdater.WAITING_FOR_WAITING_FOR_UPDATE:
            if state == UpdateControlClient.UPDATE_STATE_WAITING:
                print(f'Station {self._stationId} is waiting for an update. *** Start the update now! ***')
                self._state = StationUpdater.WAITING_FOR_UPDATE_TO_START
        elif self._state == StationUpdater.WAITING_FOR_UPDATE_TO_START:
            if state == UpdateControlClient.UPDATE_STATE_UPDATING:
                print(f'Station {self._stationId} started its update. Waiting for update to complete')
                # Release the update now
                self._mqttClient.releaseFromUpdate(self._stationId)
                self._state = StationUpdater.WAITING_FOR_UPDATE_TO_COMPLETE
            elif state == UpdateControlClient.UPDATE_STATE_NOT_WAITING:
                print(f'Station {self._stationId} aborted its update. Waiting for machine to wait for update.')
                self._state = StationUpdater.WAITING_FOR_WAITING_FOR_UPDATE
        elif self._state == StationUpdater.WAITING_FOR_UPDATE_TO_COMPLETE:
            if state == UpdateControlClient.UPDATE_STATE_UPDATE_COMPLETE:
                print(f'Station {self._stationId} completed its update. Waiting for machine to reboot')
                self._state = StationUpdater.WAITING_FOR_REBOOT
        elif self._state == StationUpdater.WAITING_FOR_REBOOT:
            if state == UpdateControlClient.UPDATE_STATE_NOT_WAITING:
                print(f'Station {self._stationId} back up after reboot.')
                self._state = StationUpdater.COMPLETE

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Invlid command arguments expect <station_id>')
    stationIds = [int(arg) for arg in sys.argv[1:]]
    cfg = loadClientConfig()
    mqttClient = UpdateControlClient(f'station-updater-0', cfg['mqtt_broker'], cfg['mqtt_port'], cfg['mqtt_user_name'], cfg['mqtt_password'])
    mqttClient.connect()
    updaters = []
    threads = []
    for stationId in stationIds:
        print(f'Updating station{stationId}...')
        updater = StationUpdater(stationId, mqttClient)
        updaters.append(updater)

        thread = threading.Thread(target=updater.update)
        threads.append(thread)
        thread.start()
        
    for thread in threads:
        thread.join()

    mqttClient.disconnect()

