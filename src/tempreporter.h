#pragma once

#include <Arduino.h>
#include <DHT.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>


#define TEMP_VAR_NAME       "temp"
#define HUMIDITY_VAR_NAME   "humidity"


class TemperatureReporter
{
    public:
        TemperatureReporter(uint8_t dht_pin, uint8_t dht_type);
        void begin();
        void report();
    private:
        void sendSensorData(int temperature, int humidity);
        DHT _dht;
};
