#!/usr/bin/env python3
from climate.client import ClimateMqttClient, loadClientConfig
from climate.topics import *
import json
from stationdb import StationDatabase
import time


class DataRecorder(ClimateMqttClient):
    def __init__(self, mqttServer, port, userName, password, clientInstance = 0):
        super().__init__(f'record-server-{clientInstance}', CLIENT_STATION, mqttServer, port, userName, password, [STATION_MSG_TYPE_SENSOR_DATA])

    def run(self):
        self.connect(runForever=True)
    
    def _onMessage(self, stationId, messageType, message):
        print(f'Received message: retain={message.retain} timestamp={message.timestamp} topic="{message.topic}" payload="{message.payload}"')

        if message.retain == 1:
            print('Skipping retained message')
            return

        try:
            payloadData = json.loads(message.payload.decode('utf-8'))
        except Exception as e:
            print(f'Exception parsing message payload {message.payload}: {e}')
            return None

        self._postData(stationId, payloadData)

    def _postData(self, stationId, payloadData):
        print(f'Posting data from station {stationId} to database: {payloadData}')
        with StationDatabase() as db:
            if stationId not in db.stations:
                station = db.addStation(int(stationId), "", "")  # TODO get ip address and hostname. The location will be set later.
            else:
                station = db.stations[stationId]
            payloadData['time'] = time.time()
            station.addDataPoint(payloadData)

if __name__ == "__main__":
    cfg = loadClientConfig()
    recorder = DataRecorder(cfg['mqtt_broker'], cfg['mqtt_port'], cfg['mqtt_user_name'], cfg['mqtt_password'])
    recorder.run()