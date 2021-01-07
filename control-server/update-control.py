#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import time


class UpdateController:
    STATE_REQUESTING_STATIONS_TO_WAIT = 0
    STATE_WAIT_FOR_STATIONS_READY = 1
    STATE_WAIT_FOR_UPDATES_TO_START = 2
    STATE_STATIONS_RELEASED = 3
    def __init__(self, mqttServer, userName, password, clientInstance = 0):
        self._clientInstance = clientInstance
        self._mqttServer = mqttServer
        self._userName = userName
        self._password = password
        self._stationsWaitingForUpdate = set()
        self._connected = False
        self._stationsRequestedForUpdate = []
        self._updateDone = False
        self._state = None

    def monitor(self):
        self._start()
        self._client.loop_forever()

# TODO: This needs to be event driven. Instead of polling, provide onStationReadyForUpdate and onStationNotReadyForUpdate callbacks.
# then proceed when all are in the requested state
    def _allStationsReadyForUpdate(self):
        print('All stations are ready for update.')
        print('Waiting for stations to start update...')
        self._state = UpdateController.STATE_WAIT_FOR_UPDATES_TO_START

    def _processState(self):
        if self._state == UpdateController.STATE_WAIT_FOR_STATIONS_READY:
            for station in self._stationsRequestedForUpdate:
                if not station in self._stationsWaitingForUpdate:
                    return
            print('All stations are ready for udate')
            print(f'Waiting for stations {self._stationsRequestedForUpdate} to start update...')
            self._allStationsReadyForUpdate()
        if self._state == UpdateController.STATE_WAIT_FOR_UPDATES_TO_START:
            for station in self._stationsRequestedForUpdate:
                if station in self._stationsWaitingForUpdate:
                    return
            print(f'All updates started on stations {self._stationsRequestedForUpdate}')
            self._releaseStations()
            self._updateDone = True

    def requestUpdate(self, stationIds):
        self._stationsRequestedForUpdate = stationIds
        self._state = UpdateController.STATE_REQUESTING_STATIONS_TO_WAIT
        self._start()
        self._client.loop_start()
        try:
            print('Waiting for connection')
            while not self._connected:
                time.sleep(0.1)
            print('Connected to MQTT broker')
            try:
                print(f'Requesting stations {self._stationsRequestedForUpdate} wait for update')
                for stationId in self._stationsRequestedForUpdate:
                    self._requestUpdate(stationId)
               
                print(f'Waiting for stations {self._stationsRequestedForUpdate} to wait for update...')
                self._state = UpdateController.STATE_WAIT_FOR_STATIONS_READY
                while not self._updateDone:
                    time.sleep(3)

            finally:
                self._releaseStations()
        finally:
            self._client.loop_stop()

    def _releaseStations(self):
        if self._state != UpdateController.STATE_STATIONS_RELEASED:
            for stationId in self._stationsRequestedForUpdate:
                self._releaseUpdate(stationId)
            print(f'All stations {self._stationsRequestedForUpdate} released from updates')
            self._state = UpdateController.STATE_STATIONS_RELEASED

    def _requestUpdate(self, stationId):
        print(f'Requesting station {stationId} to wait for update')
        self._client.publish(f'climate/{stationId}/waitForUpdate', 'yes', qos=1, retain=True)

    def _releaseUpdate(self, stationId):
        print(f'Releasing station {stationId}')
        self._client.publish(f'climate/{stationId}/waitForUpdate', 'no', qos=1, retain=True)

    def _start(self):
        self._client = mqtt.Client(self._clientId)
        self._client.username_pw_set(self._userName, self._password)
        self._client._on_connect = self._on_connect
        self._client._on_message = self._on_message
        self._client.connect(self._mqttServer)
    
    def _on_connect(self, client, userdata, flags, rc):
        print(f'_on_connect: {userdata} {flags} {rc}')
        if rc == 0:
            print('Successfully connected to broker')
            print('Subscribing to climate topic')
            client.subscribe('climate/+/waitingForUpdate', qos=1)
            self._connected = True
        else:
            print(f'Error {rc} connecting to broker')
            self._connected = False

    def _on_message(self, client, userdata, message):
        print(f'Received message: retain={message.retain} timestamp={message.timestamp} topic="{message.topic}" payload="{message.payload}"')
        ret = self._parseMessage(message)
        if ret is None:
            print(f'Failed to parse message {message}')
            return
        stationId, messageType, payloadData = ret
        print(f'Received data from station {stationId}: {messageType} => {payloadData}')
        if messageType == 'waitingForUpdate':
            print(f'Station {stationId} is waiting for update: {payloadData}')
            if payloadData.lower() == 'yes':
                if self._state is None or self._state < UpdateController.STATE_WAIT_FOR_UPDATES_TO_START:
                    self._stationsWaitingForUpdate.add(stationId)
                    self._processState()
            elif stationId in self._stationsWaitingForUpdate:
                self._stationsWaitingForUpdate.remove(stationId)
                self._processState()
            print(f'Stations waiting for update: {self._stationsWaitingForUpdate}')

    def _parseMessage(self, message):
        topicParts = message.topic.split("/")
        if len(topicParts) != 3:
            print(f'Message topic parse error: {message.topic}')
            return None
        baseTopic, stationId, messageType = topicParts
        if baseTopic != 'climate':
            print(f'Message topic unexpected parse error: {message.topic}')
            return None
        try:
            stationId = int(stationId)
        except Exception as e:
            print(f'Exception parsing stationid {stationId}: {e}')
            return None
        if messageType != 'waitingForUpdate':
            return stationId, messageType, None
        try:
            payloadData = message.payload.decode('utf-8')
        except:
            print(f'Exception parsing message payload {message.payload}: {e}')
            return None
        return (stationId, messageType, payloadData)

    @property
    def _clientId(self):
        return f'update-control-{self._clientInstance}'

if __name__ == "__main__":
    recorder = UpdateController(mqttServer='172.18.1.101', userName='climate', password='Klima')
    recorder.requestUpdate([1, 2])
    # recorder.monitor()