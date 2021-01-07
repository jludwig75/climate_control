#include "tempreporter.h"

#include <PubSubClient.h>
#include <WiFiClient.h>

#include "config.h"


#define STR_HELPER(x) #x
#define STR(x) STR_HELPER(x)


TemperatureReporter::TemperatureReporter(uint8_t dht_pin, uint8_t dht_type)
    :
    _dht(dht_pin, dht_type, 11) // 11 works fine for ESP8266
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
    sendSensorData(temp_f, humidity, vcc);
}

void TemperatureReporter::sendSensorData(float temperature, int humidity, float vcc)
{
    Serial.printf("Sending sensor data: temperature=%.2f, humidity=%u, vcc=%.2f\n", temperature, humidity, vcc);

    WiFiClient wifiClient;
    PubSubClient client(wifiClient);
    client.setServer(MQTT_SERVER, MQTT_PORT);
    if (client.connect(HOST_NAME, MQTT_USERNAME, MQTT_PASSWORD))
    {
        auto dataString = "{\"temperature\": " + String(temperature) +
                            ", \"humidity\": " + String(humidity) +
                            ", \"vcc\": " + String(vcc) + "}";
        client.publish("climate/" STR(STATION_ID), dataString.c_str(), true);
    }
}

