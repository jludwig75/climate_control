from climate.client import ClimateMqttClient, TEST_ID_BASE
from climate.topics import *
import json


class SchedulerClient(ClimateMqttClient):
    def __init__(self, controllerId, mqttServer, port, userName, password, clientInstance = 0):
        super().__init__(f'scheduler-{clientInstance}', CLIENT_SCHEDULER, mqttServer, port, userName, password)
        self._controllerId = controllerId
    
    def setMode(self, mode):
        self.publish(self._controllerId, SCEHDULE_MSG_SET_MODE, json.dumps(mode), qos=1, retain=True)

