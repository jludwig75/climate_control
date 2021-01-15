import json

TEST_ID_BASE = int(1e6)

def loadClientConfig():
    with open('config.json') as f:
        return json.loads(f.read())

class _PublishRequest:
    def __init__(self, stationId, messageType, payload, qos, retain, properties):
        self.stationId = stationId
        self.messageType = messageType
        self.payload = payload
        self.qos = qos
        self.retain = retain
        self.properties = properties

class ClimateMqttClient:
    publishedRequests = []
    def __init__(self,
                    clientId,
                    clientType,
                    ip,
                    port,
                    user,
                    passwd,
                    subscribedMessageMap = None,
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
        pass

    def publish(self, stationId, messageType, payload=None, qos=0, retain=False, properties=None):
        ClimateMqttClient.publishedRequests.append(_PublishRequest(stationId, messageType, payload, qos, retain, properties))

    def disconnect(self):
        pass
