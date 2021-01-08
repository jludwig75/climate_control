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
    ~MqttClient();
    bool connect();
    void disconnect();
    void sendSensorData(float temperature, int humidity, float vcc);
    enum UpdateState
    {
        UNKNOWN,
        UPDATE_STATE_NOT_WAITING,
        UPDATE_STATE_WAITING,
        UPDATE_STATE_UPDATING,
        UPDATE_STATE_UPDATE_COMPLETE
    };
    bool waitForUpdate() const;
    void sendUpdateState(UpdateState state);
    void loop();
protected:
    static void callback(char* topic, byte* payload, unsigned int length);
    void onMessage(char* topic, byte* payload, unsigned int length);
private:
    const char* _clientId;
    IPAddress _ip;
    uint16_t _port;
    const char *_user;
    const char *_pass;
    WiFiClient _wifiClient;
    PubSubClient _client;
    bool _waitForUpdate;
};
