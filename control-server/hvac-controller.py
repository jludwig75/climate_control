#!/usr/bin/env python3
from climate.client import ClimateMqttClient, loadClientConfig
from climate.topics import *


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
        self._mode = HVAC_MODE_OFF

    def run(self):
        self.connect(runForever=True)
    
    def _onIinit(self):
        self._setMode(self._mode)

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

    def _setMode(self, mode):
        # TODO: Apply policy checks here
        self._mode = mode
        print(f'HVAC controller {self._stationId} mode set to {self._mode}')
        self._reportMode()

    def _reportMode(self):
        self.publish(self._stationId, HVAC_MSG_TYPE_CURRENT_MODE, self._mode, qos=1, retain=True)

if __name__ == "__main__":
    cfg = loadClientConfig()
    hvacController = HvacController('hvac-controller-0', 0, cfg['mqtt_broker'], cfg['mqtt_port'], cfg['mqtt_user_name'], cfg['mqtt_password'])
    hvacController.run()