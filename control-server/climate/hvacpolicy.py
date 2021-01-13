from climate.topics import *
import json
import time


# TODO, TODO, TODO: Need to figure out how to do maximum runtime

class HvacControllerPolicy:
    def __init__(self):
        with open ('hvac_policy.json') as f:
            self._HVAC_POLICY = json.loads(f.read())

    def processModeRequest(self, currentMode, currentModeExpiration, requestedMode):
        if currentModeExpiration is None:
            if self._minimumRunTimeForMode(currentMode) > 0:
                return (None, time.time() + self._minimumRunTimeForMode(currentMode))
            else:
                currentModeExpiration = time.time()

        if requestedMode == currentMode:
            return (None, currentModeExpiration)
        newMode = None
        if time.time() >= currentModeExpiration:    # Make sure the current mode time has expired
            if self._runDownTime(currentMode) > 0:   # If the current mode has a minimum run-dow time,
                # I think it's best to handle automatic run-down after heating and cooling.
                # I think most equipment does this anyway.
                # Ignore the requested mode
                newMode = HVAC_MODE_FAN
                currentModeExpiration = time.time() + self._runDownTime(currentMode)
            else:
                newMode = requestedMode
                currentModeExpiration = time.time() + self._minimumRunTimeForMode(requestedMode)
        return (newMode, currentModeExpiration)

    def _minimumRunTimeForMode(self, mode):
        if mode in self._HVAC_POLICY:
            return self._HVAC_POLICY[mode]['minimum_runtime'] # Required attribute
        return 0

    def _runDownTime(self, mode):
        if mode in self._HVAC_POLICY and 'rundown_time' in self._HVAC_POLICY[mode]:
            return max(self._HVAC_POLICY[mode]['rundown_time'], self._HVAC_POLICY[HVAC_MODE_FAN]['minimum_runtime'])
        return 0
