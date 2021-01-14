#!/usr/bin/env python3
import sys
import time
import unittest

sys.modules['climate.hvacpolicy'] = __import__('mockhvacpolicy')
sys.modules['climate.client'] = __import__('mockclient')


from climate.topics import *
from climate.hvaccontroller import HvacController
from climate.hvacpolicy import HvacControllerPolicy
from climate.client import ClimateMqttClient

class Msg:
    def __init__(self, mode):
        self.payload = mode.encode('utf-8')

TEST_ID_BASE = int(1e6)
TEST_CONTROLLER_ID = TEST_ID_BASE


class HvacControllerUnitTest(unittest.TestCase):
    def testSetRequestedModeImmediately(self):
        controller = HvacController('test-hvac-controller-0', TEST_CONTROLLER_ID, "", 0, "", "")
        controller._onIinit()
        time.sleep(0.1)

        HvacControllerPolicy.mockNextCall((HVAC_MODE_FAN, time.time()))
        controller._onMessage(TEST_CONTROLLER_ID, HVAC_MSG_TYPE_REQUEST_MODE, Msg(HVAC_MODE_FAN))

        self.assertEqual(controller._timer, None)

        self.assertEqual(len(ClimateMqttClient.publishedRequests), 1)
        publishRequest = ClimateMqttClient.publishedRequests.pop(0)
        self.assertEqual(publishRequest.stationId, TEST_CONTROLLER_ID)
        self.assertEqual(publishRequest.messageType, HVAC_MSG_TYPE_CURRENT_MODE)
        self.assertEqual(publishRequest.payload, HVAC_MODE_FAN)

    def testSetNotRequestedModeImmediately(self):
        controller = HvacController('test-hvac-controller-0', TEST_CONTROLLER_ID, "", 0, "", "")
        controller._onIinit()
        time.sleep(0.1)

        # This node does not make sense, but it doesn't matter for this test.
        HvacControllerPolicy.mockNextCall((HVAC_MODE_COOL, time.time() + 0.1))
        controller._onMessage(TEST_CONTROLLER_ID, HVAC_MSG_TYPE_REQUEST_MODE, Msg(HVAC_MODE_FAN))

        self.assertNotEqual(controller._timer, None)

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