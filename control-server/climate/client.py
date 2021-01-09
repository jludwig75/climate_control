import paho.mqtt.client as mqtt


class ClimateMqttClient:
    def __init__(self, clientId, ip, port, user, passwd, subscribedMessageTypes = None, subscriptionClientId = None):
        self._clientId = clientId
        self._mqttServer = ip
        self._port = port
        self._userName = user
        self._password = passwd
        self._subscribedMessageTypes = subscribedMessageTypes
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
        else:
            print(f'Error {rc} connecting to broker')
            self._connected = False

    def _handleSubscriptions(self):
        if self._subscribedMessageTypes is not None and len(self._subscribedMessageTypes) > 0:
            for messageType in self._subscribedMessageTypes:
                clientIdPathPart = '+'
                if self._subscriptionClientId is not None:
                    clientIdPathPart = str(self._subscriptionClientId)
                subscriptionPath = f'climate/{clientIdPathPart}/{messageType}'
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

    def _parseMessage(self, message):
        topicParts = message.topic.split("/")
        if len(topicParts) != 3:
            print(f'Message topic parse error: {message.topic}')
            return None
        baseTopic, stationId, messageType = topicParts

        if baseTopic != 'climate' or messageType not in self._subscribedMessageTypes:
            print(f'Message type does not match subscription: {message.topic}')
            return None

        try:
            stationId = int(stationId)
        except Exception as e:
            print(f'Exception parsing stationid {stationId} from message topic {message.topic}: {e}')
            return None
        
        return (stationId, messageType)

    def disconnect(self):
        print('Disconnecting from MQTT broker')
        self._client.disconnect()
        print('Disconnected from MQTT broker')
        self._client.loop_stop()
