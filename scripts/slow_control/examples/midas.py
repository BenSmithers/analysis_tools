
import mysql.connector
from tqdm import tqdm 


print("Opening MySQL connection to neutsrv2")
mydb = mysql.connector.connect(
    host="neutsrv2.triumf.ca",
    user="history_reader",
    password="reader_PsFtKL5kR3",
    database="history"
)

print(mydb)
cursor = mydb.cursor()


print("Show all tables")
tables = []
cursor.execute("SHOW TABLES")
for x in cursor:
    
    tables.append(str(x[0]))
    print(tables[-1])

cursor.execute("describe mpmtmon_e001")
for x in cursor:
    print(x)

print("\nget data for 5 minutes on April 20, 2025")

cursor.execute("select _i_time,m001_brb_press_temp,m001_brb_pressure from mpmtmon_e001 where _i_time > 1745208120 and _i_time < 1745208420")
for x in cursor:
    print(x)

