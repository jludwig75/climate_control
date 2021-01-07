#!/usr/bin/env python3
import mariadb
import sys
from datetime import datetime, timedelta


sourceConnection = mariadb.connect(
        user='climate',
        password='Redhorn!1',
        host=sys.argv[1],
        database='climate'
    )

localConnection = mariadb.connect(
        user='climate',
        password='Redhorn!1',
        host='localhost',
        database='climate'
    )


sourceCursor = sourceConnection.cursor()
localCursor = localConnection.cursor()

def toDbString(x):
    if isinstance(x, datetime):
        x -= timedelta(hours=7)
    if x is None:
        return 'null'
    x = str(x)
    if ' ' in x:
        x = f"'{x}'"
    return x

sourceCursor.execute("SELECT id, station_id, time, temperature, humidity, vcc FROM sensor_data ORDER BY time")
for row in sourceCursor:
    strValues = [toDbString(x) for x in row]
    query = f"INSERT into sensor_data (id, station_id, time, temperature, humidity, vcc) VALUES ({','.join(strValues)})"
    print(query)
    localCursor.execute(query)
localConnection.commit()