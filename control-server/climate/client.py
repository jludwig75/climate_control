from climate.topics import *
import json
import paho.mqtt.client as mqtt


TEST_ID_BASE = int(1e6)

def loadClientConfig():
    with open('config.json') as f:
        return json.loads(f.read())

class ClimateMqttClient:
    def __init__(self,
                    clientId,
                    clientType,
                    ip,
                    port,
                    user,
                    passwd,
                    subscribedMessageMap = {},
                    subscriptionClientId = None):
        self._clientId = clientId
        self._clientType = clientType
        self._mqttServer = ip
        self._port = port
        self._userName = user
        self._password = passwd
        self._subscribedMessageMap = subscribedMessageMap
        self._subscribedClientTypes = [k for k in subscribedMessageMap.keys()]
        self._subscriptionClientId = subscriptionClientId

    def connect(self, runForever = False):
        print('Connecting to MQTT broker...')
        self._client = mqtt.Client(self._clientId)
        self._client.username_pw_set(self._userName, self._password)
        self._client._on_connect = self._on_connect
        self._client._on_message = self._on_message
        self._client.connect(self._mqttServer)
        print('Connected to MQTT broker')
        if runForever:
            self._client.loop_forever()
        else:
            self._client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        # print(f'_on_connect: {userdata} {flags} {rc}')
        if rc == 0:
            print('Successfully connected to broker')
            self._handleSubscriptions()
            self._onIinit()
        else:
            print(f'Error {rc} connecting to broker')
            self._connected = False

    def _handleSubscriptions(self):
        if self._subscribedMessageMap is not None and len(self._subscribedMessageMap.keys()) > 0:
            for clientType, messageTypes in self._subscribedMessageMap.items():
                for messageType in messageTypes:
                    clientIdPathPart = '+'
                    if self._subscriptionClientId is not None:
                        clientIdPathPart = str(self._subscriptionClientId)
                    subscriptionPath = f'{TOPIC_ROOT}/{clientType}/{clientIdPathPart}/{messageType}'
                    print(f'Subscribing to {subscriptionPath}')
                    self._client.subscribe(subscriptionPath, qos=1)

    def _on_message(self, client, userdata, message):
        # print(f'Received message: retain={message.retain} timestamp={message.timestamp} topic="{message.topic}" payload="{message.payload}"')
        ret = self._parseMessage(message)
        if ret is None:
            return
        stationId, messageType = ret
        self._onMessage(stationId, messageType, message)

    def _onMessage(self, stationId, messageType, message):
        assert False # Must be overridden by derived class
    
    def _onIinit(self):
        pass # can be overridden by derived class

    def _parseMessage(self, message):
        topicParts = message.topic.split("/")
        if len(topicParts) != 4:
            print(f'Message topic parse error: {message.topic}')
            return None
        baseTopic, clientType, stationId, messageType = topicParts

        if baseTopic != 'climate' or clientType not in self._subscribedMessageMap.keys() or messageType not in self._subscribedMessageMap[clientType]:
            print(f'Message type does not match subscription: {message.topic}')
            return None

        try:
            stationId = int(stationId)
        except Exception as e:
            print(f'Exception parsing stationid {stationId} from message topic {message.topic}: {e}')
            return None
        
        return (stationId, messageType)

    def publish(self, stationId, messageType, payload=None, qos=0, retain=False, properties=None):
        self._client.publish(f'{TOPIC_ROOT}/{self._clientType}/{stationId}/{messageType}', payload, qos=qos, retain=retain, properties=properties)

    def disconnect(self):
        print('Disconnecting from MQTT broker...')
        self._client.disconnect()
        print('Disconnected from MQTT broker')
        self._client.loop_stop()
