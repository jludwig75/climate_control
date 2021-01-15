#!/usr/bin/env python3
from climate.client import loadClientConfig
from climate.record import DataRecorder


if __name__ == "__main__":
    cfg = loadClientConfig()
    recorder = DataRecorder(cfg['mqtt_broker'], cfg['mqtt_port'], cfg['mqtt_user_name'], cfg['mqtt_password'])
    recorder.run()