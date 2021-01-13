#!/usr/bin/env python3
import json
import os
import shutil
import sys
import time
import unittest

sys.path.append('..')

from climate.hvacpolicy import HvacControllerPolicy
from climate.topics import *

with open ('hvac_policy.json') as f:
    HVAC_POLICY = json.loads(f.read())

def timesAreApproximatelyEqual(t1, t2):
    return abs(t2 - t1) < 0.01

TEST_MATRIX = {
    HVAC_MODE_OFF: {
        HVAC_MODE_OFF: {
                'mode': None,
                'duration': 0
            },
        HVAC_MODE_FAN: {
                'mode': HVAC_MODE_FAN,
                'duration': HVAC_POLICY[HVAC_MODE_FAN]['minimum_runtime']
            },
        HVAC_MODE_HEAT: {
                'mode': HVAC_MODE_HEAT,
                'duration': HVAC_POLICY[HVAC_MODE_HEAT]['minimum_runtime']
            },
        HVAC_MODE_COOL: {
                'mode': HVAC_MODE_COOL,
                'duration': HVAC_POLICY[HVAC_MODE_COOL]['minimum_runtime']
            },
    },
    HVAC_MODE_FAN: {
        HVAC_MODE_OFF: {
                'mode': HVAC_MODE_OFF,
                'duration': HVAC_POLICY[HVAC_MODE_OFF]['minimum_runtime']
            },
        HVAC_MODE_FAN: {
                'mode': None,
                'duration': 0
            },
        HVAC_MODE_HEAT: {
                'mode': HVAC_MODE_HEAT,
                'duration': HVAC_POLICY[HVAC_MODE_HEAT]['minimum_runtime']
            },
        HVAC_MODE_COOL: {
                'mode': HVAC_MODE_COOL,
                'duration': HVAC_POLICY[HVAC_MODE_COOL]['minimum_runtime']
            },
    },
    HVAC_MODE_HEAT: {
        HVAC_MODE_OFF: {
                'mode': HVAC_MODE_FAN,
                'duration': HVAC_POLICY[HVAC_MODE_HEAT]['rundown_time']
            },
        HVAC_MODE_FAN: {
                'mode': HVAC_MODE_FAN,
                'duration': HVAC_POLICY[HVAC_MODE_HEAT]['rundown_time']
            },
        HVAC_MODE_HEAT: {
                'mode': None,
                'duration': 0
            },
        HVAC_MODE_COOL: {
                'mode': HVAC_MODE_FAN,
                'duration': HVAC_POLICY[HVAC_MODE_HEAT]['rundown_time']
            },
    },
    HVAC_MODE_COOL: {
        HVAC_MODE_OFF: {
                'mode': HVAC_MODE_FAN,
                'duration': HVAC_POLICY[HVAC_MODE_COOL]['rundown_time']
            },
        HVAC_MODE_FAN: {
                'mode': HVAC_MODE_FAN,
                'duration': HVAC_POLICY[HVAC_MODE_COOL]['rundown_time']
            },
        HVAC_MODE_HEAT: {
                'mode': HVAC_MODE_FAN,
                'duration': HVAC_POLICY[HVAC_MODE_COOL]['rundown_time']
            },
        HVAC_MODE_COOL: {
                'mode': None,
                'duration': 0
            },
    }
}

class HvacPolicyUnitTest(unittest.TestCase):
    def testModeMatix(self):
        policy = HvacControllerPolicy()
        for currentMode, transitions in TEST_MATRIX.items():
            for newMode, expectedResults in transitions.items():
                # print(f'{currentMode} => {newMode}')
                now = time.time()
                newMode, expiration = policy.processModeRequest(currentMode, now, newMode)
                projectedExpirationTime = now + expectedResults['duration']
                self.assertTrue(timesAreApproximatelyEqual(expiration, projectedExpirationTime))
                self.assertEqual(newMode, expectedResults['mode'])

    def testModeMatixPreviousModeNotExpired(self):
        policy = HvacControllerPolicy()
        for currentMode, transitions in TEST_MATRIX.items():
            for newMode, expectedResults in transitions.items():
                # print(f'{currentMode} => {newMode}')
                expiration = time.time() + 1
                newMode, expiration = policy.processModeRequest(currentMode, expiration, newMode)
                projectedExpirationTime = expiration
                self.assertEqual(expiration, projectedExpirationTime)
                self.assertEqual(newMode, None) # No change

    def testModeMatixNoCurrentExpiration(self):
        policy = HvacControllerPolicy()
        # for currentMode in [HVAC_MODE_OFF, HVAC_MODE_FAN, HVAC_MODE_HEAT, HVAC_MODE_COOL]:
        #     for newMode in [HVAC_MODE_OFF, HVAC_MODE_FAN, HVAC_MODE_HEAT, HVAC_MODE_COOL]:

        for currentMode, transitions in TEST_MATRIX.items():
            for newMode, expectedResults in transitions.items():
                # print(f'{currentMode} => {newMode}')
                newMode, expiration = policy.processModeRequest(currentMode, None, newMode)
                if currentMode != HVAC_MODE_OFF:
                    projectedExpirationTime = time.time() + HVAC_POLICY[currentMode]['minimum_runtime']
                    self.assertTrue(timesAreApproximatelyEqual(expiration, projectedExpirationTime))
                    self.assertEqual(newMode, None) # No change
                else:
                    projectedExpirationTime = time.time() + expectedResults['duration']
                    self.assertTrue(timesAreApproximatelyEqual(expiration, projectedExpirationTime))
                    self.assertEqual(newMode, expectedResults['mode'])

    ## This test is redundant, but serve as a unit test for testModeMatrix
    def testTransitionsToSelf(self):
        policy = HvacControllerPolicy()
        for mode in TEST_MATRIX.keys():
            expiration = time.time()
            newMode, expiration = policy.processModeRequest(mode, expiration, mode)
            self.assertEqual(expiration, expiration)
            self.assertEqual(newMode, None) # No change

            expiration = time.time() + 1
            newMode, expiration = policy.processModeRequest(mode, expiration, mode)
            self.assertEqual(expiration, expiration)
            self.assertEqual(newMode, None) # No change

    ### The following tests are redundant, but they are crucial to prevent
    ### damage to the HVAC system:
    # They also serve as tests to verify that testModeMatrix works
    ### From Heat ###
    def testHeatToOff(self):
        policy = HvacControllerPolicy()
        now = time.time()
        newMode, expiration = policy.processModeRequest(HVAC_MODE_HEAT, now, HVAC_MODE_OFF)
        projectedTime = now + HVAC_POLICY[HVAC_MODE_HEAT]['rundown_time']
        self.assertTrue(timesAreApproximatelyEqual(expiration, projectedTime))
        self.assertEqual(newMode, HVAC_MODE_FAN)    # Run-down required

    def testHeatToFan(self):
        policy = HvacControllerPolicy()
        now = time.time()
        newMode, expiration = policy.processModeRequest(HVAC_MODE_HEAT, now, HVAC_MODE_FAN)
        projectedTime = now + HVAC_POLICY[HVAC_MODE_HEAT]['rundown_time']
        self.assertTrue(timesAreApproximatelyEqual(expiration, projectedTime))
        self.assertEqual(newMode, HVAC_MODE_FAN)

    def testHeatToCool(self):
        policy = HvacControllerPolicy()
        now = time.time()
        newMode, expiration = policy.processModeRequest(HVAC_MODE_HEAT, now, HVAC_MODE_COOL)
        projectedTime = now + HVAC_POLICY[HVAC_MODE_HEAT]['rundown_time']
        self.assertTrue(timesAreApproximatelyEqual(expiration, projectedTime))
        self.assertEqual(newMode, HVAC_MODE_FAN)    # Run-down required

    ### From Cool ###
    def testCoolToOff(self):
        policy = HvacControllerPolicy()
        now = time.time()
        newMode, expiration = policy.processModeRequest(HVAC_MODE_COOL, now, HVAC_MODE_OFF)
        projectedTime = now + HVAC_POLICY[HVAC_MODE_COOL]['rundown_time']
        self.assertTrue(timesAreApproximatelyEqual(expiration, projectedTime))
        self.assertEqual(newMode, HVAC_MODE_FAN)    # Run-down required

    def testCoolToFan(self):
        policy = HvacControllerPolicy()
        now = time.time()
        newMode, expiration = policy.processModeRequest(HVAC_MODE_COOL, now, HVAC_MODE_FAN)
        projectedTime = now + HVAC_POLICY[HVAC_MODE_COOL]['rundown_time']
        self.assertTrue(timesAreApproximatelyEqual(expiration, projectedTime))
        self.assertEqual(newMode, HVAC_MODE_FAN)

    def testCoolToHeat(self):
        policy = HvacControllerPolicy()
        now = time.time()
        newMode, expiration = policy.processModeRequest(HVAC_MODE_COOL, now, HVAC_MODE_HEAT)
        projectedTime = now + HVAC_POLICY[HVAC_MODE_COOL]['rundown_time']
        self.assertTrue(timesAreApproximatelyEqual(expiration, projectedTime))
        self.assertEqual(newMode, HVAC_MODE_FAN)    # Run-down required


if __name__ == '__main__':
    unittest.main()