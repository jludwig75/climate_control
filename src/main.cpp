#include <Arduino.h>
#include <BasicWifi.h>
#include "tempreporter.h"
#include "update.h"


ADC_MODE(ADC_VCC);


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

void blinkLed(int blinkCount, int onTimeMs, int offTimeMs)
{
    uint8_t ledPin = LED_BUILTIN;
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, HIGH);

    for (auto i = 0; i < blinkCount; i++)
    {
        digitalWrite(ledPin, LOW);
        delay(onTimeMs);
        digitalWrite(ledPin, HIGH);
        delay(offTimeMs);
    }
}

void setup()
{
    Serial.begin(115200);

    Serial.println("\r\nStarting temperature sensor");

    reporter.begin();    // initialize temperature reporter first so the HW has time to initialize

    if (wifi_setup(HOST_NAME, WIFI_SSID, WIFI_PASSWORD, 10 * 1000))    // 10 seconde timeout
    {
        Serial.println("Waiting for DHT...");
        delay(500);    // TODO: Might not need it with the WiFi conneciton time

        reporter.report();
    }
    else
    {
        Serial.println("Failed to initialize WiFi!");
        // blink LED several times to show an error.
        blinkLed(20, 100, 400); // 20 0.5 second intervals = 10 seconds duration. On 20% of interval. Should look like an error. :)
    }
}

void loop()
{
    if (!checkForUpdate())
    {
        Serial.println("Sleeping...");
        ESP.deepSleep(report_interval_ms * 1000);
    }
}