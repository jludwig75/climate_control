from climate.topics import *
import time


# TODO, TODO, TODO: Need to figure out how to do maximum runtime

class HvacControllerPolicy:
    _nextCallReturn = None
    @staticmethod
    def mockNextCall(data):
        HvacControllerPolicy._nextCallReturn = data

    def processModeRequest(self, currentMode, currentModeExpiration, requestedMode):
        return HvacControllerPolicy._nextCallReturn
