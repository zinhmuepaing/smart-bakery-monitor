#db.py for datastorage in Web Application

import mysql.connector
from datetime import datetime

def write_database(temp,humid,f):
    now = datetime.now()
    datetime_string = now.strftime("%Y-%m-%d %H")
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='iotpdb'
    )
    cursor = conn.cursor()

    # Insert data (replace column names with your actual columns)
    sql = "INSERT INTO datas (Date, Temperature, Humidity,FireStatus) VALUES (%s, %s, %s, %s)"
    values = (datetime_string,temp ,humid ,str(f))

    cursor.execute(sql, values)

    # Commit the transaction
    conn.commit()

    print(f"{cursor.rowcount} record inserted.")

    cursor.close()
    conn.close()