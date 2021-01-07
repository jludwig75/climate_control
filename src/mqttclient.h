#pragma once


#include <PubSubClient.h>
#include <WiFiClient.h>


class MqttClient
{
public:
    MqttClient(const char* clientId,
                const IPAddress& ip,
                uint16_t port,
                const char *user,
                const char *pass);
    bool connect();
    void disconnect();
    void sendSensorData(float temperature, int humidity, float vcc);
    void sendWaitingForUpdate(bool waiting);
private:
    const char* _clientId;
    IPAddress _ip;
    uint16_t _port;
    const char *_user;
    const char *_pass;
    WiFiClient _wifiClient;
    PubSubClient _client;
};
