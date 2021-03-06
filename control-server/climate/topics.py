TOPIC_ROOT='climate'

CLIENT_STATION='station'
CLIENT_HVAC_CONTROLLER='hvac'
CLIENT_SCHEDULER='schedule'

STATION_MSG_TYPE_SENSOR_DATA='sensorData'
STATION_MSG_TYPE_UPDATE_STATE='updateState'
STATION_MSG_TYPE_WAIT_FOR_UPDATE='waitForUpdate'

HVAC_MSG_TYPE_REQUEST_MODE='requestMode'
HVAC_MSG_TYPE_CURRENT_MODE='currentMode'

HVAC_MODE_OFF="Off"
HVAC_MODE_FAN="Fan"
HVAC_MODE_HEAT="Heat"
HVAC_MODE_COOL="Cool"

SCEHDULE_MSG_SET_MODE="setMode"

"""
Conversations
=============
Note: broker is omitted where not necessary to be show

Sensor Update
-------------
    station client --> "climate/station/<id>/sensorData", "{"temperature": float, "humidity": int, "vcc": float}" --> update client

Station Update
--------------
    On normal run when starting up after sending temperature (as is works)
    station client --> "climate/station/<id>/updateState", "NotWaiting" --> update client

    station client <-- "climage/<id>/waitForUpdate", "yes" <-- update client
    station client initialzies OTA
    station client --> "climate/station/<id>/updateState", "Waiting" --> update client

    station client <-- OTA start <-- PlatformIO
    station client --> "climate/station/<id>/updateState", "Updating" --> update client
    station client <-- OTA end <-- PlatformIO
    station client --> "climate/station/<id>/updateState", "UpdateComplete" --> update client

HVAC Controller
------------------
    control server --> "climate/hvac/<id>/requestMode", "Off, Fan, Heat, Cool" --> HVAC controller
    control server <-- "climate/hvac/<id>/currentMode", "Off, Fan, Heat, Cool" <-- HVAC controller

Schedule Update
---------------
    scheduler --> "climate/schedule/<id>/setMode", "{ "Heat": float, "cool": float }" --> Control Server  (One of "Heat" or "Cool" or both, empty to shut off)

"""

