#include "mqttclient.h"

#include <PubSubClient.h>
#include <WiFiClient.h>

#include "config.h"


#define STR_HELPER(x) #x
#define STR(x) STR_HELPER(x)


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
    _client(_wifiClient)
{
}


bool MqttClient::connect()
{
    Serial.printf("setServer(%s, %u)\n", _ip.toString().c_str(), _port);
    _client.setServer(_ip, _port);
    Serial.printf("connect(\"%s\", \"%s\", \"%s\")\n", _clientId, _user, _pass);
    return _client.connect(_clientId, _user, _pass);
}

void MqttClient::disconnect()
{
    _client.disconnect();
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
    if (!_client.publish("climate/" STR(STATION_ID) "/sensorData", dataString.c_str(), true))
    {
        Serial.println("Failed to publish sensor data");
        return;
    }
}

void MqttClient::sendWaitingForUpdate(bool waiting)
{
    const char* state = (waiting ? "yes" : "no");
    Serial.printf("Preparing to bublishing waiting for update: \"%s\"\n", state);

    if (!_client.connected())
    {
        Serial.println("MQTT client no longer connected. Reconnecting...");
        if (!connect())
        {
            Serial.println("Reconnecte failed");
            return;
        }
    }

    Serial.printf("Publishing waiting for update: \"%s\"\n", state);
    if (!_client.publish("climate/" STR(STATION_ID) "/waitingForUpdate", state, true))
    {
        Serial.printf("Failed to publish waiting for update: \"%s\"\n", state);
    }
}
