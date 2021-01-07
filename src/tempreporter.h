#pragma once

#include <Arduino.h>
#include <DHT.h>


#define TEMP_VAR_NAME       "temp"
#define HUMIDITY_VAR_NAME   "humidity"
#define VCC_VAR_NAME        "vcc"


class MqttClient;


class TemperatureReporter
{
    public:
        TemperatureReporter(uint8_t dht_pin, uint8_t dht_type, MqttClient& mqttClient);
        void begin();
        void report();
    private:
        DHT _dht;
        MqttClient& _mqttClient;
};
