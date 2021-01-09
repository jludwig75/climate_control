#include "mqttclient.h"

#include <PubSubClient.h>
#include <WiFiClient.h>

#include "config.h"


#define STR_HELPER(x) #x
#define STR(x) STR_HELPER(x)

MqttClient* _this = NULL;

void MqttClient::callback(char* topic, byte* payload, unsigned int length)
{
    Serial.print("Message arrived [");
    Serial.print(topic);
    Serial.print("] ");
    for (decltype(length) i = 0; i < length; i++)
    {
        Serial.print((char)payload[i]);
    }
    Serial.println();
    _this->onMessage(topic, payload, length);
}


MqttClient::UpdateState fromString(const std::string& stateString)
{
    if (stateString == "NotWaiting")
    {
        return MqttClient::UPDATE_STATE_NOT_WAITING;
    }
    if (stateString == "Waiting")
    {
        return MqttClient::UPDATE_STATE_WAITING;
    }
    if (stateString == "Updating")
    {
        return MqttClient::UPDATE_STATE_UPDATING;
    }
    if (stateString == "UpdateComplete")
    {
        return MqttClient::MqttClient::UPDATE_STATE_UPDATE_COMPLETE;
    }

    return MqttClient::UNKNOWN;
}

const char* toString(MqttClient::UpdateState state)
{
    switch (state)
    {
    case MqttClient::UPDATE_STATE_NOT_WAITING:
        return "NotWaiting";
    case MqttClient::UPDATE_STATE_WAITING:
        return "Waiting";
    case MqttClient::UPDATE_STATE_UPDATING:
        return "Updating";
    case MqttClient::UPDATE_STATE_UPDATE_COMPLETE:
        return "UpdateComplete";
    default:
        return "UNKNOWN";
    }
}


MqttClient::MqttClient(const char* clientId,
                const IPAddress& ip,
                uint16_t port,
                const char *user,
                const char *pass)
    :
    _clientId(clientId),
    _ip(ip),
    _port(port),
    _user(user),
    _pass(pass),
    _wifiClient(),
    _client(_wifiClient),
    _waitForUpdate(false)
{
    _this = this;
}

MqttClient::~MqttClient()
{
    _this = NULL;
}


void MqttClient::onMessage(char* topic, byte* payload, unsigned int length)
{
    // TODO: Validate the topic

    _waitForUpdate = strncasecmp((const char *)payload, "yes", length) == 0;
}

bool MqttClient::connect()
{
    Serial.printf("setServer(%s, %u)\n", _ip.toString().c_str(), _port);
    _client.setServer(_ip, _port);
    _client.setCallback(callback);
    Serial.printf("connect(\"%s\", \"%s\", \"%s\")\n", _clientId, _user, _pass);
    if (!_client.connect(_clientId, _user, _pass))
    {
        Serial.printf("Failed to connect to MQTT broker with clientID \"%s\" and username \"%s\"\n", _clientId, _user);
        return false;
    }

    Serial.print("Subscribing to ");
    Serial.println("climate/station/" STR(STATION_ID) "/waitForUpdate");
    if (!_client.subscribe("climate/station/" STR(STATION_ID) "/waitForUpdate", 1))
    {
        Serial.println("Failed to subscribe to waitForUpdate");
        disconnect();
        return false;
    }

    return true;
}

void MqttClient::disconnect()
{
    _client.disconnect();
}

bool MqttClient::waitForUpdate() const
{
    return _waitForUpdate;
}

void MqttClient::sendSensorData(float temperature, int humidity, float vcc)
{
    Serial.printf("Sending sensor data: temperature=%.2f, humidity=%u, vcc=%.2f\n", temperature, humidity, vcc);

    if (!_client.connected())
    {
        Serial.println("MQTT client no longer connected. Reconnecting...");
        if (!connect())
        {
            Serial.println("Reconnecte failed");
            return;
        }
    }

    auto dataString = "{\"temperature\": " + String(temperature) +
                        ", \"humidity\": " + String(humidity) +
                        ", \"vcc\": " + String(vcc) + "}";
    if (!_client.publish("climate/station/" STR(STATION_ID) "/sensorData", dataString.c_str(), true))
    {
        Serial.println("Failed to publish sensor data");
        return;
    }
}

void MqttClient::sendUpdateState(UpdateState state)
{
    Serial.printf("Preparing to bublishing waiting for update: \"%s\"\n", toString(state));

    if (!_client.connected())
    {
        Serial.println("MQTT client no longer connected. Reconnecting...");
        if (!connect())
        {
            Serial.println("Reconnecte failed");
            return;
        }
    }

    Serial.printf("Publishing waiting for update: \"%s\"\n", toString(state));
    if (!_client.publish("climate/station/" STR(STATION_ID) "/updateState", toString(state), true)) // TODO: QoS 1
    {
        Serial.printf("Failed to publish waiting for update: \"%s\"\n", toString(state));
    }
}

void MqttClient::loop()
{
    _client.loop();
}
