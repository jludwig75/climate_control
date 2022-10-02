#include <Arduino.h>
#include <BasicWifi.h>
#include "mqttclient.h"
#include "tempreporter.h"
#include "update.h"


ADC_MODE(ADC_VCC);


/* NOTE: please add this file (config.h) and define the following in it:
#define WIFI_SSID       "SSID Name"
#define WIFI_PASSWORD   "SSID Password"

#define MQTT_SERVER     IPAddress(192,168,0,101)
#define MQTT_PORT       1883
#define MQTT_USERNAME   "user"
#define MQTT_PASSWORD   "passwd"

#define DHT_TYPE    DHT22

#define REPORT_INTERVAL_MINUTES 1
*/
#include "config.h" // <= This file is not part of the repo code. You must add it. See above. ^^^


const unsigned long report_interval_ms = REPORT_INTERVAL_MINUTES * 60 * 1000;              // interval at which to read sensor in ms

MqttClient mqttClient(HOST_NAME, MQTT_SERVER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD);

TemperatureReporter reporter(DHT_PIN, DHT_TYPE, mqttClient);

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


static bool runMain()
{
    if (!wifi_setup(HOST_NAME, WIFI_SSID, WIFI_PASSWORD, 10 * 1000))    // 10 seconde timeout
    {
        Serial.println("Failed to setup WiFi");
        return false;
    }

    Serial.println("Waiting for DHT...");
    delay(500);    // TODO: Might not need it with the WiFi conneciton time

    if (!mqttClient.connect())
    {
        Serial.println("Failed to connect to MQTT broker");
        return false;
    }

    reporter.report();
    return true;
}

unsigned long startTime = 0;

void setup()
{
    Serial.begin(115200);

    Serial.println("\r\nStarting temperature sensor");

    reporter.begin();    // initialize temperature reporter first so the HW has time to initialize

    if (!runMain())
    {
        Serial.println("Failed to initialize WiFi!");
        // blink LED several times to show an error.
        blinkLed(20, 100, 400); // 20 0.5 second intervals = 10 seconds duration. On 20% of interval. Should look like an error. :)
    }

    startTime = millis();
}

void loop()
{
    mqttClient.loop();
    if (millis() - startTime < 1000)
    {
        // Give the MQTT client time to receive any retained message
        return;
    }
    if (!checkForUpdate(mqttClient))
    {
        Serial.println("Sleeping...");
        ESP.deepSleep(report_interval_ms * 1000);
    }
}