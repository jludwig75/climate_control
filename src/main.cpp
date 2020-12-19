#include <Arduino.h>
#include <BasicWifi.h>
#include "tempreporter.h"


/* NOTE: please add this file (config.h) and define the following in it:
#define WIFI_SSID       "SSID Name"
#define WIFI_PASSWORD   "SSID Password"
#define HOST_NAME       "Desired host name"

#define DHT_TYPE    DHT22
#define DHT_PIN     2

#define STATION_ID              2
#define REPORT_INTERVAL_MINUTES 1
#define REPORT_URL              "http://172.18.1.65:8080/report_sensor_data"
*/
#include "config.h" // <= This file is not part of the repo code. You must add it. See above. ^^^


const unsigned long report_interval_ms = REPORT_INTERVAL_MINUTES * 60 * 1000;              // interval at which to read sensor in ms

TemperatureReporter reporter(DHT_PIN, DHT_TYPE);

void setup()
{
    Serial.begin(115200);

    reporter.begin();    // initialize temperature reporter

    if (!wifi_setup(HOST_NAME, WIFI_SSID, WIFI_PASSWORD, 3))    // 3 Retries
    {
        Serial.println("Failed to initialize WiFi!");
        // TODO: blink LED several times
    }
    else
    {
        Serial.println("\r\nWaiting for DHT...");
        delay(500);    // TODO: Might not need it with the WiFi conneciton time

        reporter.report();
    }

    Serial.println("Sleeping...");
    ESP.deepSleep(report_interval_ms * 1000);
}

void loop()
{
}