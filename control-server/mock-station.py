#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import sys
import time


"""
Conversation:

    On normal run when starting up after sending temperature (as is works)
    station client --- "climate/<id>/updateState", "NotWaiting" --> broker --> update client

    station client <-- "climage/<id>/waitForUpdate", "yes" <-- update client
    station client initialzies OTA
    station client --- "climate/<id>/updateState", "Waiting" --> update client

    station client <-- OTA start <-- PlatformIO
    station client --- "climate/<id>/updateState", "Updating" --> update client
    station client <-- OTA end <-- PlatformIO
    station client --- "climate/<id>/updateState", "UpdateComplete" --> update client


"""

report_interval_ms = 60 * 1000

def millis():
    return int(time.time() * 1000)

def delay(ms):
    time.sleep(ms / 1000.0)

class PowerException(Exception):
    MODE_REBOOT = 0
    MODE_DEEP_SLEEP = 1
    def __init__(self, mode, sleepTime = None):
        super().__init__('Mode exception')
        self._mode = mode
        if mode == PowerException.MODE_DEEP_SLEEP:
            assert sleepTime is not None
        self._sleepTime = sleepTime

    @property
    def mode(self):
        return self._mode
    
    @property
    def sleepTime(self):
        return self._sleepTime

class Esp:
    def deepSleep(self, intervalNs):
        raise PowerException(PowerException.MODE_DEEP_SLEEP, intervalNs / 1000)
    def reboot(self):
        raise PowerException(PowerException.MODE_REBOOT)

ESP = Esp()

class MqttClient:
    def __init__(self, clientId, ip, port, user, passwd, stationId):
        self._clientId = clientId
        self._mqttServer = ip
        self._port = port
        self._userName = user
        self._password = passwd
        self._stationId = stationId
        self._waitForUpdate = False

    def connect(self):
        print('Connecting to MQTT broker...')
        self._client = mqtt.Client(self._clientId)
        self._client.username_pw_set(self._userName, self._password)
        self._client._on_connect = self._on_connect
        self._client._on_message = self._on_message
        self._client.connect(self._mqttServer)
        print('Connected to MQTT broker')
        self._client.loop_start()

    @property
    def waitForUpdate(self):
        return self._waitForUpdate

    def _on_connect(self, client, userdata, flags, rc):
        # print(f'_on_connect: {userdata} {flags} {rc}')
        if rc == 0:
            print('Successfully connected to broker')
            print('Subscribing to climate topic')
            self._client.subscribe('climate/+/waitForUpdate', qos=1)
        else:
            print(f'Error {rc} connecting to broker')
            self._connected = False

    def _on_message(self, client, userdata, message):
        # print(f'Received message: retain={message.retain} timestamp={message.timestamp} topic="{message.topic}" payload="{message.payload}"')
        ret = self._parseMessage(message)
        if ret is None:
            return
        stationId, messageType, payloadData = ret
        print(f'Received data from station {stationId}: {messageType} => {payloadData}')
        self._waitForUpdate = True if payloadData.lower() == 'yes' else False

    def _parseMessage(self, message):
        topicParts = message.topic.split("/")
        if len(topicParts) != 3:
            print(f'Message topic parse error: {message.topic}')
            return None
        baseTopic, stationId, messageType = topicParts

        if baseTopic != 'climate' or messageType != 'waitForUpdate':
            print(f'Message type does not match subscription: {message.topic}')
            return None

        try:
            stationId = int(stationId)
        except Exception as e:
            print(f'Exception parsing stationid {stationId}: {e}')
            return None
        
        if stationId != self._stationId:
            # print('Ignoring message not for this station')
            return None

        try:
            payloadData = message.payload.decode('utf-8')
        except:
            print(f'Exception parsing message payload {message.payload}: {e}')
            return None
        return (stationId, messageType, payloadData)

    def disconnect(self):
        print('Disconnecting from MQTT broker')
        self._client.disconnect()
        print('Disconnected from MQTT broker')
        self._client.loop_stop()

    UPDATE_STATE_NOT_WAITING = 'NotWaiting'
    UPDATE_STATE_WAITING = 'Waiting'
    UPDATE_STATE_UPDATING = 'Updating'
    UPDATE_STATE_UPDATE_COMPLETE = 'UpdateComplete'
    def sendUpdateState(self, state):
        print(f'Station {self._stationId} sending update state "{state}"')
        self._client.publish(f'climate/{self._stationId}/updateState', state, qos=1, retain=True)


class OTA:
    STATE_WIATING = 0
    STATE_RUNNING = 1
    STATE_COMPLETE = 2
    def __init__(self):
        self._startTime = millis()
        self._state = OTA.STATE_WIATING

    def ota_setup(self, onStart, onEnd):
        self._onStart = onStart
        self._onEnd = onEnd

    def ota_onLoop(self):
        if self._state == OTA.STATE_WIATING:
            if millis() - self._startTime > 8 * 1000:
                print('OTA Start')
                self._onStart()
                self._state = OTA.STATE_RUNNING
        elif self._state == OTA.STATE_RUNNING:
            if millis() - self._startTime > 23 * 1000:
                print('OTA End')
                self._onEnd()
                print('OTA Rebooting ESP')
                ESP.reboot()

class Station:
    def __init__(self, id):
        self._id = id

    def run(self):
        while True:
            try:
                self._setup()
                while True:
                    self._loop()
            except PowerException as e:
                if e.mode == PowerException.MODE_DEEP_SLEEP:
                    time.sleep(e.sleepTime / 1000.0)
                else:
                    time.sleep(3)

    def _setup(self):
        print('Running sketch...')
        self._mqttClient = MqttClient(f'dummy-station-{self._id}', '172.18.1.101', 1883, 'climate', 'Klima', self._id)
        self._ota = OTA()
        self._lastUpdateCheck = 0
        self._otaInitialized = False
        self._updating = False
        self._mqttClient.connect()
        print('Waiting for MQTT...')
        delay(1000) # Give MQTT a chance to connect
        print('End setup')

    def _loop(self):
        if not self._checkForUpdate():
            print('Sleeping...')
            ESP.deepSleep(report_interval_ms * 1000)

    def _checkForUpdate(self):
        t = millis()
        if self._lastUpdateCheck == 0 or t - self._lastUpdateCheck > 30 * 1000:
            self._lastUpdateCheck = t
            if not self._updating and not self._mqttClient.waitForUpdate:
                self._mqttClient.sendUpdateState(MqttClient.UPDATE_STATE_NOT_WAITING)
                print("Disconnecting mqtt client...")
                self._mqttClient.disconnect()
                return False
            if not self._otaInitialized:
                print('Initializing OTA code')
                self._ota.ota_setup(self._onOtaStart, self._onOtaEnd)
                self._mqttClient.sendUpdateState(MqttClient.UPDATE_STATE_WAITING)
                self._otaInitialized = True

        if self._otaInitialized:
            self._ota.ota_onLoop()
        return True
    
    def _onOtaStart(self):
        self._updating = True
        self._mqttClient.sendUpdateState(MqttClient.UPDATE_STATE_UPDATING)
    
    def _onOtaEnd(self):
        self._mqttClient.sendUpdateState(MqttClient.UPDATE_STATE_UPDATE_COMPLETE)
        self._mqttClient.disconnect()
        self._updating = False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Invlid command arguments expect <station_id>')
        stationId = 11
    else:
        stationId = int(sys.argv[1])
    print(f'Simulating station {stationId}...')
    station = Station(stationId)
    station.run()