#!/usr/bin/env python3
from climate.hvaccontroller import HvacController
from climate.client import loadClientConfig


if __name__ == "__main__":
    cfg = loadClientConfig()
    hvacController = HvacController('hvac-controller-0', 0, cfg['mqtt_broker'], cfg['mqtt_port'], cfg['mqtt_user_name'], cfg['mqtt_password'])
    hvacController.run()