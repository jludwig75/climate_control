#!/usr/bin/env python3
from argparse import ArgumentParser
from climate.client import loadClientConfig
from climate.schedule import SchedulerClient
from climate.topics import *
import json


CONTROLLER_ID=0


if __name__ == "__main__":
    parser = ArgumentParser(usage='Change the thermostat mode')

    parser.add_argument('-H', '--heat', type=float, default=None, help='The heating set point')
    parser.add_argument('-C', '--cool', type=float, default=None, help='The cooling set point')

    args = parser.parse_args()

    modeRequest = {}
    if args.heat is not None:
        modeRequest[HVAC_MODE_HEAT] = args.heat
    if args.cool is not None:
        modeRequest[HVAC_MODE_COOL] = args.cool
    
    print(f'Mode request: {modeRequest}')

    cfg = loadClientConfig()

    shedulerClient = SchedulerClient(CONTROLLER_ID, cfg['mqtt_broker'], cfg['mqtt_port'], cfg['mqtt_user_name'], cfg['mqtt_password'])
    shedulerClient.connect()
    shedulerClient.setMode(modeRequest)
    shedulerClient.disconnect()