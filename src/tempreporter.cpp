#include "tempreporter.h"

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
    int temp_f = _dht.readTemperature(true);     // Read temperature as Fahrenheit
    sendSensorData(temp_f, humidity);
}

void TemperatureReporter::sendSensorData(int temperature, int humidity)
{
    Serial.printf("Sending sensor data: temperature=%u, humidity=%u\n", temperature, humidity);

    WiFiClient wifiClient;
    HTTPClient httpClient;

    httpClient.begin(wifiClient, REPORT_URL);
    httpClient.addHeader("Content-Type", "application/x-www-form-urlencoded");

    String postData = String("station_id=") + String(STATION_ID) + "&" + TEMP_VAR_NAME + "=" + String(temperature) + "&" + HUMIDITY_VAR_NAME + "=" + String(humidity);
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

