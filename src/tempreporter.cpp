#include "tempreporter.h"

#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

#include <PubSubClient.h>

#include "config.h"


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

    {
        WiFiClient wifiClient;
        PubSubClient client(wifiClient);
        client.setServer(MQTT_SERVER, MQTT_PORT);
        if (client.connect(HOST_NAME, MQTT_USERNAME, MQTT_PASSWORD))
        {
            auto dataString = "{\"temperature\": " + String(temperature) +
                                ", \"humidity\": " + String(humidity) +
                                ", \"vcc\": " + String(vcc) + "}";
            client.publish("climate/" HOST_NAME, dataString.c_str());
        }
    }

    {
        WiFiClient wifiClient;
        HTTPClient httpClient;

        httpClient.begin(wifiClient, REPORT_URL);
        httpClient.addHeader("Content-Type", "application/x-www-form-urlencoded");

        String postData = String("station_id=") + String(STATION_ID) + "&" +
                            TEMP_VAR_NAME + "=" + String(temperature) + "&" +
                            HUMIDITY_VAR_NAME + "=" + String(humidity) + "&" +
                            VCC_VAR_NAME + "=" + String(vcc);
        auto httpCode = httpClient.POST(postData);
        if (httpCode == HTTP_CODE_OK)
        {
            Serial.printf("Successfully sent sensor data\n");
        }
        else
        {
            Serial.printf("HTTP error %u sending sensor data\n", httpCode);
        }

        httpClient.end();
    }
}

