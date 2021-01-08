#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import sys
import threading
import time

class MqttClient:
    def __init__(self, clientId, ip, port, user, passwd):
        self._clientId = clientId
        self._mqttServer = ip
        self._port = port
        self._userName = user
        self._password = passwd
        self._waitForUpdate = False
        self._stationStates = {}
        self._stationStateChangeCallbacks = {}

    def connect(self):
        print('Connecting to MQTT broker...')
        self._client = mqtt.Client(self._clientId)
        self._client.username_pw_set(self._userName, self._password)
        self._client._on_connect = self._on_connect
        self._client._on_message = self._on_message
        self._client.connect(self._mqttServer)
        print('Connected to MQTT broker')
        self._client.loop_start()

    UPDATE_STATE_UNKNWON = 'Uknown'
    UPDATE_STATE_NOT_WAITING = 'NotWaiting'
    UPDATE_STATE_WAITING = 'Waiting'
    UPDATE_STATE_UPDATING = 'Updating'
    UPDATE_STATE_UPDATE_COMPLETE = 'UpdateComplete'
    UPDATE_STATE_INVALID = 'INVALID'
    def stationUpdateState(self, stationId):
        if stationId not in self._stationStates:
            self._stationStates[stationId] = MqttClient.UPDATE_STATE_UNKNWON
        return self._stationStates[stationId]

    def registerStateChangeCallback(self, stationId, callback):
        self._stationStateChangeCallbacks[stationId] = callback

    def _on_connect(self, client, userdata, flags, rc):
        # print(f'_on_connect: {userdata} {flags} {rc}')
        if rc == 0:
            print('Successfully connected to broker')
            print('Subscribing to climate topic')
            self._client.subscribe('climate/+/updateState', qos=1)
        else:
            print(f'Error {rc} connecting to broker')
            self._connected = False

    def _on_message(self, client, userdata, message):
        # print(f'Received message: retain={message.retain} timestamp={message.timestamp} topic="{message.topic}" payload="{message.payload}"')
        ret = self._parseMessage(message)
        if ret is None:
            return
        stationId, messageType, payloadData = ret
        # print(f'Received data from station {stationId}: {messageType} => {payloadData}')

        if stationId not in self._stationStates:
            self._stationStates[stationId] = MqttClient.UPDATE_STATE_UNKNWON

        if payloadData in [MqttClient.UPDATE_STATE_NOT_WAITING, MqttClient.UPDATE_STATE_WAITING, MqttClient.UPDATE_STATE_UPDATING, MqttClient.UPDATE_STATE_UPDATE_COMPLETE]:
            self._stationStates[stationId] = payloadData
        else:
            self._stationStates[stationId] = MqttClient.UPDATE_STATE_INVALID
        # print(f'Station {stationId} update state: {self._stationStates[stationId]}')
        if stationId in self._stationStateChangeCallbacks:
            self._stationStateChangeCallbacks[stationId](self._stationStates[stationId])

    def _parseMessage(self, message):
        topicParts = message.topic.split("/")
        if len(topicParts) != 3:
            print(f'Message topic parse error: {message.topic}')
            return None
        baseTopic, stationId, messageType = topicParts

        if baseTopic != 'climate' or messageType != 'updateState':
            print(f'Message type does not match subscription: {message.topic}')
            return None

        try:
            stationId = int(stationId)
        except Exception as e:
            print(f'Exception parsing stationid {stationId} from message topic {message.topic}: {e}')
            return None
        
        try:
            payloadData = message.payload.decode('utf-8')
        except:
            print(f'Exception parsing message payload {message.payload}: {e}')
            return None
        return (stationId, messageType, payloadData)

    def disconnect(self):
        print('Disconnecting from MQTT broker')
        self._client.disconnect()
        print('Disconnected from MQTT broker')
        self._client.loop_stop()
    
    def requestUpdate(self, stationId):
        self._client.publish(f'climate/{stationId}/waitForUpdate', 'yes', qos=1, retain=True)
    
    def releaseFromUpdate(self, stationId):
        self._client.publish(f'climate/{stationId}/waitForUpdate', 'no', qos=1, retain=True)


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
            if state == MqttClient.UPDATE_STATE_WAITING:
                print(f'Station {self._stationId} is waiting for an update. *** Start the update now! ***')
                self._state = StationUpdater.WAITING_FOR_UPDATE_TO_START
        elif self._state == StationUpdater.WAITING_FOR_UPDATE_TO_START:
            if state == MqttClient.UPDATE_STATE_UPDATING:
                print(f'Station {self._stationId} started its update. Waiting for update to complete')
                # Release the update now
                self._mqttClient.releaseFromUpdate(self._stationId)
                self._state = StationUpdater.WAITING_FOR_UPDATE_TO_COMPLETE
            elif state == MqttClient.UPDATE_STATE_NOT_WAITING:
                print(f'Station {self._stationId} aborted its update. Waiting for machine to wait for update.')
                self._state = StationUpdater.WAITING_FOR_WAITING_FOR_UPDATE
        elif self._state == StationUpdater.WAITING_FOR_UPDATE_TO_COMPLETE:
            if state == MqttClient.UPDATE_STATE_UPDATE_COMPLETE:
                print(f'Station {self._stationId} completed its update. Waiting for machine to reboot')
                self._state = StationUpdater.WAITING_FOR_REBOOT
        elif self._state == StationUpdater.WAITING_FOR_REBOOT:
            if state == MqttClient.UPDATE_STATE_NOT_WAITING:
                print(f'Station {self._stationId} back up after reboot.')
                self._state = StationUpdater.COMPLETE

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Invlid command arguments expect <station_id>')
    stationIds = [int(arg) for arg in sys.argv[1:]]
    mqttClient = MqttClient(f'dummy-station-0', '172.18.1.101', 1883, 'climate', 'Klima')
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

