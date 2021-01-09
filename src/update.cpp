#include "update.h"

#include <BasicOTA.h>
// #include <ESP8266HTTPClient.h>
// #include <WiFiClient.h>

#include "config.h" // <= This file is not part of the repo code. You must add it. See above. ^^^
#include "mqttclient.h"


static bool otaInitialized = false;
static unsigned long lastUpdateCheck = 0;
static bool updating = false;

bool checkForUpdate(MqttClient& mqttClient)
{
    auto t = millis();
    if (lastUpdateCheck == 0 || (t - lastUpdateCheck) >= 30 * 1000)
    {
        lastUpdateCheck = t;
        if (!updating && !mqttClient.waitForUpdate())
        {
            mqttClient.sendUpdateState(MqttClient::UPDATE_STATE_NOT_WAITING);
            Serial.println("Disconnecting mqtt client...");
            mqttClient.disconnect();
            return false;
        }

        if (!otaInitialized)
        {
            Serial.println("Initializing OTA code");
            ota_setup(HOST_NAME, OTA_PASSWORD,
                        [&mqttClient]{  // onOTAStart
                            updating = true;
                            mqttClient.sendUpdateState(MqttClient::UPDATE_STATE_UPDATING);
                        },
                        [&mqttClient]{  // onOTAEnd
                            mqttClient.sendUpdateState(MqttClient::UPDATE_STATE_UPDATE_COMPLETE);
                            Serial.println("Disconnecting mqtt client...");
                            mqttClient.disconnect();
                            updating = false;
                        });
            mqttClient.sendUpdateState(MqttClient::UPDATE_STATE_WAITING);
            otaInitialized = true;
        }
    }

    if (otaInitialized) // TODO: Should be an assert
    {
        ota_onLoop();
    }

    return true;
}