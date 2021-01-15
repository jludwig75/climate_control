#!/usr/bin/env python3
from climate.client import ClimateMqttClient, TEST_ID_BASE
from climate.control import ControlServer
from climate.topics import *
import json
import time
import unittest


TEST_CONTROLLER_ID = TEST_ID_BASE
TEST_HVAC_ID = TEST_ID_BASE + 1

TEST_STATION1_ID = TEST_ID_BASE
TEST_STATION2_ID = TEST_ID_BASE + 1
TEST_STATION3_ID = TEST_ID_BASE + 2
TEST_STATION_IDS = [TEST_STATION1_ID, TEST_STATION2_ID, TEST_STATION3_ID]


class MockHvacController(ClimateMqttClient):
    def __init__(self):
        super().__init__('test-controller-0',
                        CLIENT_HVAC_CONTROLLER,
                        '172.18.1.101',
                        0,
                        'climate',
                        'Klima',
                        subscribedMessageMap={ CLIENT_HVAC_CONTROLLER: [HVAC_MSG_TYPE_REQUEST_MODE] },
                        subscriptionClientId=TEST_HVAC_ID)
        self.retainedMessages = []
        self.messages = []
    def _onMessage(self, stationId, messageType, message):
        class _ClimateMqttMessage:
            def __init__(self, stationId, messageType, message):
                self.stationId = stationId
                self.messageType = messageType
                self.message = message
        class _HvacControllerMqttMessage(_ClimateMqttMessage):
            def __init__(self, stationId, messageType, message):
                super().__init__(stationId, messageType, message)
                self.mode = message.payload.decode('utf-8')

        if message.retain:
            print(f'Recevied retained message {stationId, messageType, message.payload}')
            self.retainedMessages.append(_HvacControllerMqttMessage(stationId, messageType, message))
        else:
            print(f'Recevied message {stationId, messageType, message.payload}')
            self.messages.append(_HvacControllerMqttMessage(stationId, messageType, message))

class TestStation(ClimateMqttClient):
    def __init__(self):
        super().__init__('test-client-0',
                        CLIENT_STATION,
                        '172.18.1.101',
                        1883,
                        'climate',
                        'Klima')
        self.retainedMessages = []
        self.messages = []
    def _onIinit(self):
        for stationId in TEST_STATION_IDS:
            self.publish(stationId, STATION_MSG_TYPE_SENSOR_DATA, None, qos=1, retain=True)

def mkSensorData(temperature, humidity=40, vcc=3.4):
    return json.dumps({'temperature': temperature, 'humidity': humidity, 'vcc': vcc})

class ControlServerIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.hvac = MockHvacController()
        self.hvac.connect()

        self.control = ControlServer('test-control-server-0',
                                     TEST_CONTROLLER_ID,
                                     TEST_HVAC_ID,
                                     '172.18.1.101',
                                     1883,
                                     'climate',
                                     'Klima',
                                     True)
        self.control.connect()

        self.station = TestStation()
        self.station.connect()

        time.sleep(0.1)
    
    def tearDown(self):
        self.station.disconnect()
        self.control.disconnect()
        self.hvac.disconnect()

    def testTemperatureBelowSetPointRequestsHeat(self):
        self.station.publish(TEST_STATION1_ID, STATION_MSG_TYPE_SENSOR_DATA, mkSensorData(60))
        time.sleep(0.05)
        self.assertEqual(len(self.hvac.messages), 1)
        message = self.hvac.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_REQUEST_MODE)
        self.assertEqual(message.mode, HVAC_MODE_HEAT)

    def testTemperatureAboveSetPointRequestsCool(self):
        self.station.publish(TEST_STATION1_ID, STATION_MSG_TYPE_SENSOR_DATA, mkSensorData(80))
        time.sleep(0.05)
        self.assertEqual(len(self.hvac.messages), 1)
        message = self.hvac.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_REQUEST_MODE)
        self.assertEqual(message.mode, HVAC_MODE_COOL)

    def testVaryingTemperature(self):
        self.station.publish(TEST_STATION1_ID, STATION_MSG_TYPE_SENSOR_DATA, mkSensorData(60))
        time.sleep(0.05)

        self.assertEqual(len(self.hvac.messages), 1)
        message = self.hvac.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_REQUEST_MODE)
        self.assertEqual(message.mode, HVAC_MODE_HEAT)


        self.station.publish(TEST_STATION1_ID, STATION_MSG_TYPE_SENSOR_DATA, mkSensorData(63))
        time.sleep(0.05)

        self.assertEqual(len(self.hvac.messages), 1)
        message = self.hvac.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_REQUEST_MODE)
        self.assertEqual(message.mode, HVAC_MODE_HEAT)


        self.station.publish(TEST_STATION1_ID, STATION_MSG_TYPE_SENSOR_DATA, mkSensorData(69))
        time.sleep(0.05)

        self.assertEqual(len(self.hvac.messages), 1)
        message = self.hvac.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_REQUEST_MODE)
        self.assertEqual(message.mode, HVAC_MODE_FAN)


        self.station.publish(TEST_STATION1_ID, STATION_MSG_TYPE_SENSOR_DATA, mkSensorData(80))
        time.sleep(0.05)

        self.assertEqual(len(self.hvac.messages), 1)
        message = self.hvac.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_REQUEST_MODE)
        self.assertEqual(message.mode, HVAC_MODE_COOL)

if __name__ == '__main__':
    unittest.main()