TOPIC_ROOT='climate'
CLIENT_STATION='station'

STATION_MSG_TYPE_SENSOR_DATA='sensorData'

STATION_MSG_TYPE_UPDATE_STATE='updateState'
STATION_MSG_TYPE_WAIT_FOR_UPDATE='waitForUpdate'

"""
Conversation:

STATION UPDATE:

    On normal run when starting up after sending temperature (as is works)
    station client --- "climate/station/<id>/updateState", "NotWaiting" --> broker --> update client

    station client <-- "climage/<id>/waitForUpdate", "yes" <-- update client
    station client initialzies OTA
    station client --- "climate/station/<id>/updateState", "Waiting" --> update client

    station client <-- OTA start <-- PlatformIO
    station client --- "climate/station/<id>/updateState", "Updating" --> update client
    station client <-- OTA end <-- PlatformIO
    station client --- "climate/station/<id>/updateState", "UpdateComplete" --> update client

"""

