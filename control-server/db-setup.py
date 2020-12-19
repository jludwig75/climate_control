#!/usr/bin/env python3
import mariadb


def createDabase():
    conn = mariadb.connect(
            user='climate',
            password='Redhorn!1',
            host='localhost'
        )

    with conn.cursor() as cursor:
        cursor.execute('SHOW DATABASES')
        for (database,) in cursor:
            if database == 'climate':
                return

        cursor.execute('CREATE DATABASE climate')

CREATE_STATION_SQL ="""
CREATE TABLE station (
        id INT NOT NULL PRIMARY KEY,
        ip_address VARCHAR(16) NOT NULL,
        host_name VARCHAR(64),
        LOCATION VARCHAR(255) )
"""

CREATE_SENSOR_DATA_SQL = """
CREATE TABLE sensor_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        station_id INT NOT NULL,
        time TIMESTAMP NOT NULL,
        temperature INT NOT NULL,
        humidity INT,
        INDEX(station_id),
        CONSTRAINT `fk_data_station`
            FOREIGN KEY (station_id) REFERENCES station (id)
            ON DELETE CASCADE
    )
""" # Not sure if ON DELETE CASCADE makes sense

def createTables():
    conn = mariadb.connect(
            user='climate',
            password='Redhorn!1',
            host='localhost',
            database='climate'
        )

    with conn.cursor() as cursor:
        # Only for a destructive re-create
        # cursor.execute('DROP TABLE station')
        # cursor.execute('DROP TABLE sensor_data')

        cursor.execute('SHOW TABLES')
        tables = [row[0] for row in cursor]
        if not 'station' in tables:
            cursor.execute(CREATE_STATION_SQL)
        if not 'sensor_data' in tables:
            cursor.execute(CREATE_SENSOR_DATA_SQL)

def main():
    createDabase()
    createTables()

if __name__ == "__main__":
    main()