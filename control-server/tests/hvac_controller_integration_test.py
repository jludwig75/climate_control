#!/usr/bin/env python3
from climate.client import ClimateMqttClient
from climate.hvaccontroller import HvacController
from climate.topics import *
import json
import time
import unittest


TEST_ID_BASE = int(1e6)
TEST_CONTROLLER_ID = TEST_ID_BASE


class TestMqttClient(ClimateMqttClient):
    def __init__(self):
        super().__init__("test-client-0",
                        CLIENT_HVAC_CONTROLLER,
                        '172.18.1.101',
                        0,
                        'climate',
                        'Klima',
                        subscribedMessageMap={ CLIENT_HVAC_CONTROLLER: [HVAC_MSG_TYPE_CURRENT_MODE] },
                        subscriptionClientId=TEST_CONTROLLER_ID)
        self.retainedMessages = []
        self.messages = []
    def _onMessage(self, stationId, messageType, message):
        class _ClimateMqttMessage:
            def __init__(self, stationId, messageType, message):
                self.stationId = stationId
                self.messageType = messageType
                self.message = message

        if message.retain:
            self.retainedMessages.append(_ClimateMqttMessage(stationId, messageType, message))
        else:
            self.messages.append(_ClimateMqttMessage(stationId, messageType, message))
    def requestMode(self, mode):
        self.publish(TEST_CONTROLLER_ID, HVAC_MSG_TYPE_REQUEST_MODE, mode, qos=1, retain=True)

with open ('hvac_policy.json') as f:
    HVAC_POLICY = json.loads(f.read())

class HvacControllerIntegrationTest(unittest.TestCase):
    def setUp(self):
        print('setUp')
        self.testClient = TestMqttClient()
        self.testClient.connect()
        self.testClient.requestMode(HVAC_MODE_OFF)
        self.testClient.disconnect()
        self.testClient.messages.clear()
        time.sleep(HVAC_POLICY[HVAC_MODE_OFF]['minimum_runtime'])
        self.controller = HvacController('test-hvac-controller-0',
                                            TEST_CONTROLLER_ID,
                                            '172.18.1.101',
                                            0,
                                            'climate',
                                            'Klima')
        self.controller.run(False)
        self.testClient.connect()
        time.sleep(0.01)    # Give clients time to receive retained messages

    def tearDown(self):
        self.testClient.requestMode(HVAC_MODE_OFF)
        time.sleep(0.01)    # Give controller time to receive messages and for current mode to run down
        self.controller.disconnect()
        self.testClient.disconnect()
    
    def testTurnOnFan(self):
        self.testClient.requestMode(HVAC_MODE_FAN)
        time.sleep(0.01)    # Give client enough time to receive current mode message from controller
        self.assertEqual(len(self.testClient.messages), 1)
        message = self.testClient.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_CURRENT_MODE)

if __name__ == '__main__':
    unittest.main()