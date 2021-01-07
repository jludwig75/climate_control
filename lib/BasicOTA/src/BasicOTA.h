#pragma once

#include <functional>


void ota_setup(const char* hostName, const char* password, std::function<void(void)> onOTAStart);
void ota_onLoop();
