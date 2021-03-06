#!/usr/bin/env python3
import sys
import time
import unittest

sys.modules['climate.hvacpolicy'] = __import__('mockhvacpolicy')
sys.modules['climate.client'] = __import__('mockclient')


from climate.topics import *
from climate.hvaccontroller import HvacController
from climate.hvacpolicy import HvacControllerPolicy
from climate.client import ClimateMqttClient, TEST_ID_BASE

class Msg:
    def __init__(self, mode):
        self.payload = mode.encode('utf-8')

TEST_CONTROLLER_ID = TEST_ID_BASE

class HvacControllerUnitTest(unittest.TestCase):
    def setUp(self):
        self.controller = HvacController('test-hvac-controller-0', TEST_CONTROLLER_ID, "", 0, "", "", True)
        self.controller._onIinit()
        time.sleep(0.1)
        ClimateMqttClient.publishedRequests.clear()

    def testSetRequestedModeImmediately(self):
        HvacControllerPolicy.mockNextCall((HVAC_MODE_FAN, time.time()))
        self.controller._onMessage(TEST_CONTROLLER_ID, HVAC_MSG_TYPE_REQUEST_MODE, Msg(HVAC_MODE_FAN))

        self.assertEqual(self.controller._timer, None)

        self.assertEqual(len(ClimateMqttClient.publishedRequests), 1)
        publishRequest = ClimateMqttClient.publishedRequests.pop(0)
        self.assertEqual(publishRequest.stationId, TEST_CONTROLLER_ID)
        self.assertEqual(publishRequest.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(publishRequest.payload, HVAC_MODE_FAN)

    def testSetNotRequestedModeImmediately(self):
        # This node does not make sense, but it doesn't matter for this test.
        HvacControllerPolicy.mockNextCall((HVAC_MODE_COOL, time.time() + 0.1))
        self.controller._onMessage(TEST_CONTROLLER_ID, HVAC_MSG_TYPE_REQUEST_MODE, Msg(HVAC_MODE_FAN))

        self.assertNotEqual(self.controller._timer, None)

        self.assertEqual(len(ClimateMqttClient.publishedRequests), 1)
        publishRequest = ClimateMqttClient.publishedRequests.pop(0)
        self.assertEqual(publishRequest.stationId, TEST_CONTROLLER_ID)
        self.assertEqual(publishRequest.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(publishRequest.payload, HVAC_MODE_COOL)

        HvacControllerPolicy.mockNextCall((HVAC_MODE_FAN, time.time() + 0.2))
        time.sleep(0.2)

        self.assertEqual(len(ClimateMqttClient.publishedRequests), 1)
        publishRequest = ClimateMqttClient.publishedRequests.pop(0)
        self.assertEqual(publishRequest.stationId, TEST_CONTROLLER_ID)
        self.assertEqual(publishRequest.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(publishRequest.payload, HVAC_MODE_FAN)

        # Make sure timer does not fire again
        time.sleep(0.2)
        self.assertEqual(len(ClimateMqttClient.publishedRequests), 0)


if __name__ == '__main__':
    unittest.main()