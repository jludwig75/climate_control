#!/usr/bin/env python3
import json
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
from stationdb import StationDatabase
import time


class DataRecorder:
    def __init__(self, mqttServer, userName, password, clientInstance = 0):
        self._clientInstance = clientInstance
        self._mqttServer = mqttServer
        self._userName = userName
        self._password = password

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
            client.subscribe('climate/#', qos=1)
        else:
            print(f'Error {rc} connecting to broker')

    def _on_message(self, client, userdata, message):
        print(f'Received message: retain={message.retain} timestamp={message.timestamp} topic="{message.topic}" payload="{message.payload}"')
        if message.retain == 1:
            print('Skipping retained message')
            return
        ret = self._parseMessage(message)
        if ret is None:
            print(f'Failed to parse message {message}')
            return
        stationId, messageType, payloadData = ret
        print(f'Received data from station {stationId}: {messageType} => {payloadData}')
        if messageType == 'sensorData':
            self._postData(stationId, payloadData)

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
        if messageType != 'sensorData':
            return stationId, messageType, None
        try:
            payloadData = json.loads(message.payload.decode('utf-8'))
        except:
            print(f'Exception parsing message payload {message.payload}: {e}')
            return None
        return (stationId, messageType, payloadData)

    def _postData(self, stationId, payloadData):
        print(f'Posting data from station {stationId} to database: {payloadData}')
        with StationDatabase() as db:
            if stationId not in db.stations:
                station = db.addStation(int(stationId), "", "")  # TODO get ip address and hostname. The location will be set later.
            else:
                station = db.stations[stationId]
            payloadData['time'] = time.time()
            station.addDataPoint(payloadData)

    @property
    def _clientId(self):
        return f'record-server-{self._clientInstance}'

if __name__ == "__main__":
    recorder = DataRecorder(mqttServer='172.18.1.101', userName='climate', password='Klima')
    recorder.run()