#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import time


class UpdateController:
    def __init__(self, mqttServer, userName, password, clientInstance = 0):
        self._clientInstance = clientInstance
        self._mqttServer = mqttServer
        self._userName = userName
        self._password = password
        self._stationsWaitingForUpdate = set()
        self._connected = False

    def monitor(self):
        self._start()
        self._client.loop_forever()

# TODO: This needs to be event driven. Instead of polling, provide onStationReadyForUpdate and onStationNotReadyForUpdate callbacks.
# then proceed when all are in the requested state
    def requestUpdate(self, stationIds):
        self._start()
        self._client.loop_start()
        try:
            print('Waiting for connection')
            while not self._connected:
                time.sleep(0.1)
            print('Connected to MQTT broker')
            try:
                print(f'Requesting stations {stationIds} wait for update')
                for stationId in stationIds:
                    self._requestUpdate(stationId)
                
                print(f'Waiting for stations {stationIds} to wait to update...')
                for stationId in stationIds:
                    while not stationId in self._stationsWaitingForUpdate:
                        print(f'Stations ready for uppdate: {self._stationsWaitingForUpdate}')
                        time.sleep(3)
                
                print('All stations are ready for update. Enter something when update complete')
                input()

                print(f'Waiting for stations {stationIds} to start update...')
                for stationId in stationIds:
                    while stationId in self._stationsWaitingForUpdate:
                        print(f'Stations ready for uppdate: {self._stationsWaitingForUpdate}')
                        time.sleep(3)

            finally:
                for stationId in stationIds:
                    self._releaseUpdate(stationId)
        finally:
            self._client.loop_stop()


    def _requestUpdate(self, stationId):
        self._client.publish(f'climate/{stationId}/waitForUpdate', 'yes', qos=1, retain=True)

    def _releaseUpdate(self, stationId):
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
                self._stationsWaitingForUpdate.add(stationId)
            elif stationId in self._stationsWaitingForUpdate:
                self._stationsWaitingForUpdate.remove(stationId)
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
    # recorder.requestUpdate([1, 2])
    recorder.monitor()