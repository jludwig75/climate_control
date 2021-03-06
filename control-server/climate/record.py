from climate.client import ClimateMqttClient, TEST_ID_BASE
from climate.stationdb import StationDatabase
from climate.topics import *
import json
import time


class DataRecorder(ClimateMqttClient):
    def __init__(self, mqttServer, port, userName, password, clientInstance = 0, testClient=False):
        super().__init__(f'record-server-{clientInstance}', CLIENT_STATION, mqttServer, port, userName, password, subscribedMessageMap={ CLIENT_STATION: [STATION_MSG_TYPE_SENSOR_DATA] })
        self._testClient = testClient

    def run(self):
        self.connect(runForever=True)
    
    def _onMessage(self, stationId, messageType, message):
        if self._testClient and stationId < TEST_ID_BASE:
            print(f'Skipping "{messageType}" message from station {stationId}')
            return
        elif not self._testClient and stationId >= TEST_ID_BASE:
            print(f'Skipping "{messageType}" message from test station {stationId}')
            return
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
