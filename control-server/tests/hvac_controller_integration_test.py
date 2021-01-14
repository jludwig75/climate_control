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
        class _HvacControllerMqttMessage(_ClimateMqttMessage):
            def __init__(self, stationId, messageType, message):
                super().__init__(stationId, messageType, message)
                self.mode = message.payload.decode('utf-8')

        if message.retain:
            self.retainedMessages.append(_HvacControllerMqttMessage(stationId, messageType, message))
        else:
            self.messages.append(_HvacControllerMqttMessage(stationId, messageType, message))
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
        self.assertEqual(message.mode, HVAC_MODE_FAN)
    
    def testTurnOnFanThenOff(self):
        self.testClient.requestMode(HVAC_MODE_FAN)

        time.sleep(0.01)    # Give client enough time to receive current mode message from controller
        self.assertEqual(len(self.testClient.messages), 1)
        message = self.testClient.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(message.mode, HVAC_MODE_FAN)

        self.testClient.requestMode(HVAC_MODE_OFF)

        time.sleep(0.01)    # Give client enough time to receive current mode message from controller,
                            # but not enough to run for the minimum runtime
        self.assertEqual(len(self.testClient.messages), 0)

        # Now wait long enough for the minimum fan run time
        time.sleep(HVAC_POLICY[HVAC_MODE_FAN]['minimum_runtime'])
        self.assertEqual(len(self.testClient.messages), 1)
        message = self.testClient.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(message.mode, HVAC_MODE_OFF)

    def testTurnOnHeat(self):
        self.testClient.requestMode(HVAC_MODE_HEAT)

        time.sleep(0.01)    # Give client enough time to receive current mode message from controller
        self.assertEqual(len(self.testClient.messages), 1)
        message = self.testClient.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(message.mode, HVAC_MODE_HEAT)

    def testTurnOnHeatThenOff(self):
        self.testClient.requestMode(HVAC_MODE_HEAT)

        time.sleep(0.01)    # Give client enough time to receive current mode message from controller
        self.assertEqual(len(self.testClient.messages), 1)
        message = self.testClient.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(message.mode, HVAC_MODE_HEAT)

        self.testClient.requestMode(HVAC_MODE_OFF)

        time.sleep(0.01)    # Give client enough time to receive current mode message from controller,
                            # but not enough to run for the minimum runtime
        self.assertEqual(len(self.testClient.messages), 0)

        # Now wait long enough for the minimum heat run time
        time.sleep(HVAC_POLICY[HVAC_MODE_HEAT]['minimum_runtime'])
        self.assertEqual(len(self.testClient.messages), 1)
        message = self.testClient.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(message.mode, HVAC_MODE_FAN)

        # Now wait long enough for the heat run-down time
        time.sleep(HVAC_POLICY[HVAC_MODE_HEAT]['rundown_time'])
        self.assertEqual(len(self.testClient.messages), 1)
        message = self.testClient.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(message.mode, HVAC_MODE_OFF)

    def testTurnOnCoolThenOff(self):
        self.testClient.requestMode(HVAC_MODE_COOL)

        time.sleep(0.01)    # Give client enough time to receive current mode message from controller
        self.assertEqual(len(self.testClient.messages), 1)
        message = self.testClient.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(message.mode, HVAC_MODE_COOL)

        self.testClient.requestMode(HVAC_MODE_OFF)

        time.sleep(0.01)    # Give client enough time to receive current mode message from controller,
                            # but not enough to run for the minimum runtime
        self.assertEqual(len(self.testClient.messages), 0)

        # Now wait long enough for the minimum cool run time
        time.sleep(HVAC_POLICY[HVAC_MODE_COOL]['minimum_runtime'])
        self.assertEqual(len(self.testClient.messages), 1)
        message = self.testClient.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(message.mode, HVAC_MODE_FAN)

        # Now wait long enough for the cool run-down time
        time.sleep(HVAC_POLICY[HVAC_MODE_COOL]['rundown_time'])
        self.assertEqual(len(self.testClient.messages), 1)
        message = self.testClient.messages.pop(0)
        self.assertEqual(message.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(message.mode, HVAC_MODE_OFF)
    
if __name__ == '__main__':
    unittest.main()