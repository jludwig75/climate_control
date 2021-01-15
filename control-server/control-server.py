#!/usr/bin/env python3
from climate.client import loadClientConfig
from climate.control import ControlServer


if __name__ == "__main__":
    cfg = loadClientConfig()
    hvacController = ControlServer('control-server-0', 0, 0, cfg['mqtt_broker'], cfg['mqtt_port'], cfg['mqtt_user_name'], cfg['mqtt_password'])
    hvacController.run()