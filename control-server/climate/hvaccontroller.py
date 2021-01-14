from climate.client import ClimateMqttClient, loadClientConfig
from climate.hvacpolicy import HvacControllerPolicy
from climate.topics import *
import threading
import time


class HvacController(ClimateMqttClient):
    def __init__(self, clientId, stationId, ip, port, user, passwd):
        self._stationId = stationId
        super().__init__(clientId,
                            CLIENT_HVAC_CONTROLLER,
                            ip,
                            port,
                            user,
                            passwd,
                            subscribedMessageMap={ CLIENT_HVAC_CONTROLLER: [HVAC_MSG_TYPE_REQUEST_MODE] },
                            subscriptionClientId=stationId)
        self._currentMode = HVAC_MODE_OFF
        self._currentModeExpiration = None
        self._policy = HvacControllerPolicy()
        self._timer = None
        self._initialized = False
        self._pendingRequestedMode = None

    def run(self, runForever=True):
        self.connect(runForever)
    
    def _onIinit(self):
        # Do this to reflect the initial start state
        self._reportMode()
        self._initialized = True
        # Now respond to any request we may have been given.
        if self._pendingRequestedMode is not None:
            self._setMode(self._pendingRequestedMode)

    def _onMessage(self, stationId, messageType, message):
        if messageType == HVAC_MSG_TYPE_REQUEST_MODE:
            if stationId != self._stationId:
                print(f'Station {self._stationId} received incorrect station id {stationId}')
                return

            try:
                mode = message.payload.decode('utf-8')
            except Exception as e:
                print(f'Exception parsing message payload {message.payload}: {e}')
                return

            if not mode in [HVAC_MODE_OFF, HVAC_MODE_FAN, HVAC_MODE_HEAT, HVAC_MODE_COOL]:
                print(f'Unsupported mode {mode} requested of station {self._stationId}')
                return
            
            self._setMode(mode)

    def _setMode(self, requestedMode):
        if not self._initialized:
            self._pendingRequestedMode = requestedMode
            return
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        newMode, self._currentModeExpiration = self._policy.processModeRequest(self._currentMode, self._currentModeExpiration, requestedMode)
        if newMode is not None and newMode != self._currentMode:
            self._currentMode = newMode
            print(f'HVAC controller {self._stationId} mode set to {self._currentMode}')
            self._reportMode()
        if newMode != requestedMode:    # Can't change to the requested mode yet
            # Set a timer to try again after the expiration
            # TODO: May need to set the timer just past this time in case the timing is off. Probably not, but maybe
            self._timer = threading.Timer(self._currentModeExpiration - time.time(), self._setMode, args=(requestedMode,))
            self._timer.start()
            return

    def _reportMode(self):
        self.publish(self._stationId, HVAC_MSG_TYPE_CURRENT_MODE, self._currentMode, qos=1, retain=True)
