#pragma once


class MqttClient;


// Returns true if the station should wait for an update
bool checkForUpdate(MqttClient& mqttClient);