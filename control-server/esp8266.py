import time


def millis():
    return int(time.time() * 1000)

def delay(ms):
    time.sleep(ms / 1000.0)

class PowerException(Exception):
    MODE_REBOOT = 0
    MODE_DEEP_SLEEP = 1
    def __init__(self, mode, sleepTime = None):
        super().__init__('Mode exception')
        self._mode = mode
        if mode == PowerException.MODE_DEEP_SLEEP:
            assert sleepTime is not None
        self._sleepTime = sleepTime

    @property
    def mode(self):
        return self._mode
    
    @property
    def sleepTime(self):
        return self._sleepTime

class Esp:
    def runSketch(self, sketch):
        while True:
            try:
                sketch.setup()
                while True:
                    sketch.loop()
            except PowerException as e:
                if e.mode == PowerException.MODE_DEEP_SLEEP:
                    time.sleep(e.sleepTime / 1000.0)
                else:
                    time.sleep(3)
    def deepSleep(self, intervalNs):
        raise PowerException(PowerException.MODE_DEEP_SLEEP, intervalNs / 1000)
    def reboot(self):
        raise PowerException(PowerException.MODE_REBOOT)

ESP = Esp()
