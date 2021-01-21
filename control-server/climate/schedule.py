from climate.client import ClimateMqttClient, TEST_ID_BASE
from climate.topics import *
import json


"""
Schedule Schema
===============

mode_change
--------
time
heat set point: can be NULL
cool set point: can be NULL
day_of_week

"""


class SchedulerClient(ClimateMqttClient):
    def __init__(self, controllerId, mqttServer, port, userName, password, clientInstance = 0):
        super().__init__(f'scheduler-{clientInstance}', CLIENT_SCHEDULER, mqttServer, port, userName, password)
        self._controllerId = controllerId
    
    def setMode(self, mode):
        self.publish(self._controllerId, SCEHDULE_MSG_SET_MODE, json.dumps(mode), qos=1, retain=True)

