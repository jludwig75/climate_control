#pragma once

#include <functional>


void ota_setup(const char* hostName, const char* password, std::function<void(void)> onOTAStart, std::function<void(void)> onOTAEnd);
void ota_onLoop();
