#include "tempreporter.h"

#include <PubSubClient.h>
#include <WiFiClient.h>

#include "config.h"
#include "mqttclient.h"


#define STR_HELPER(x) #x
#define STR(x) STR_HELPER(x)


TemperatureReporter::TemperatureReporter(uint8_t dht_pin, uint8_t dht_type, MqttClient& mqttClient)
    :
    _dht(dht_pin, dht_type),
    _mqttClient(mqttClient)
{
}

void TemperatureReporter::begin()
{
    _dht.begin();    // initialize temperature sensor
}

void TemperatureReporter::report()
{
    int humidity = _dht.readHumidity();          // Read humidity (percent)
    float temp_f = _dht.readTemperature(true);     // Read temperature as Fahrenheit
    float vcc = ESP.getVcc() / 1000.0;
    _mqttClient.sendSensorData(temp_f, humidity, vcc);
}
