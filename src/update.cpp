#include "update.h"

#include <BasicOTA.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

#include "config.h" // <= This file is not part of the repo code. You must add it. See above. ^^^

static bool updateRequested()
{
    Serial.println("Checking for update...");
    WiFiClient wifiClient;
    HTTPClient httpClient;

    httpClient.begin(wifiClient, UPDATE_CHECK_URL);

    auto responseCode = httpClient.GET();
    if (responseCode != HTTP_CODE_OK)
    {
        Serial.printf("Error: Update check failure: %u\n", responseCode);
        return false;
    }

    auto responseData = httpClient.getString();

    httpClient.end();

    Serial.printf("Check for update response: %s\n", responseData.c_str());

    return responseData == "yes";
}

static bool otaInitialized = false;
static unsigned long lastUpdateCheck = 0;

bool checkForUpdate()
{
    auto t = millis();
    if (lastUpdateCheck == 0 || (t - lastUpdateCheck) >= 30 * 1000)
    {
        lastUpdateCheck = t;
        if (!updateRequested())
        {
            return false;
        }

        if (!otaInitialized)
        {
            Serial.println("Initializing OTA code");
            ota_setup(HOST_NAME, OTA_PASSWORD);
            otaInitialized = true;
        }
    }

    if (otaInitialized) // TODO: Should be an assert
    {
        ota_onLoop();
    }

    return true;
}