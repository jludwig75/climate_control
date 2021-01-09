from test.esp8266 import ESP, millis


class OTA:
    STATE_WIATING = 0
    STATE_RUNNING = 1
    STATE_COMPLETE = 2
    def __init__(self):
        self._startTime = millis()
        self._state = OTA.STATE_WIATING

    def ota_setup(self, onStart, onEnd):
        self._onStart = onStart
        self._onEnd = onEnd

    def ota_onLoop(self):
        if self._state == OTA.STATE_WIATING:
            if millis() - self._startTime > 8 * 1000:
                print('OTA Start')
                self._onStart()
                self._state = OTA.STATE_RUNNING
        elif self._state == OTA.STATE_RUNNING:
           if millis() - self._startTime > 23 * 1000:
                print('OTA End')
                self._onEnd()
                print('OTA Rebooting ESP')
                ESP.reboot()

_ota = None

def ota_setup(onStart, onEnd):
    global _ota
    _ota = OTA()
    _ota.ota_setup(onStart, onEnd)

def ota_onLoop():
    _ota.ota_onLoop()
