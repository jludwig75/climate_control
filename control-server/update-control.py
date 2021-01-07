#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe


class UpdateController:
    def __init__(self, mqttServer, userName, password, clientInstance = 0):
        self._clientInstance = clientInstance
        self._mqttServer = mqttServer
        self._userName = userName
        self._password = password
        self._stationsWaitingForUpdate = set()

    def run(self):
        client = mqtt.Client(self._clientId)
        client.username_pw_set(self._userName, self._password)
        client._on_connect = self._on_connect
        client._on_message = self._on_message

        client.connect(self._mqttServer)

        client.loop_forever()
    
    def _on_connect(self, client, userdata, flags, rc):
        print(f'_on_connect: {userdata} {flags} {rc}')
        if rc == 0:
            print('Successfully connected to broker')
            print('Subscribing to climate topic')
            client.subscribe('climate/+/waitingForUpdate', qos=1)
        else:
            print(f'Error {rc} connecting to broker')

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
    recorder.run()