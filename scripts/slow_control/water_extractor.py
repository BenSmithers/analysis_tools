import psycopg2
import numpy as np 
import os 
import h5py as h5 
from tqdm import tqdm

"""
    Pre-caches the water system's flow rate
"""

print("Opening MySQL connection to neutsrv2")
mydb = psycopg2.connect(
    host="neutsrv2.triumf.ca",
    user="daq_reader",
    password="reader_HD3Z0GFkxMBr",
    database="daq",
    #port=5432
)
def average(thisdat, nmerge=10):
    if nmerge==1:
        return thisdat
    if int((len(thisdat)%nmerge))!=0:
        thisdat = thisdat[:-(len(thisdat)%nmerge)]
    else:
        return np.array([])
    return np.mean(np.reshape(thisdat, (int(len(thisdat)/nmerge), nmerge)), axis=1)


def sample(thisdat, group=10):
    """
        Sample 1 of every GROUP in $thisdat
    """
    if group==1:
        return thisdat 
    mask = np.arange(len(thisdat)) % group == 0
    return thisdat[mask]

cursor = mydb.cursor()

tables = []
cursor.execute("select table_schema, table_name from information_schema.tables")
for x in cursor:
    if "monitoring" in x[1] and ("1970" not in x[1]) and ("default" not in x[1]):
        tables.append(x[1])

# build up all of the table table

canonical_keys = ['FT1_Flow', 'FT1_Flowmeter_Sc', 'LT1_Level', 'LT_1_Level_Scale', 'LeakDetector', 'MixTank_High', 'MixTank_Low', 'Mix_Tank_Hi_Leve', 'PT1_Pressure', 'PT1_Pump_Pressur', 'PT2_OutputPressS', 'PT2_Pressure', 'PT3_Level', 'PT5_Depth', 'PT6_Depth', 'PT_3_Level_Scale', 'PT_5_Depth_Scale', 'PT_6_Depth_Scale', 'QC1_Conductivity', 'QC1_Resistivty_1', 'QC1_Temperature', 'QC2_Conductivity', 'QC2_Resistivty_2', 'QC2_Temperature', 'RemovalTank_High', 'Salinity', 'TDS', 'Tank_In_DIGITAL_', 'UT1_Cond_Scaled', 'UT1_Conductivity', 'UT1_Depth', 'UT1_Temperature', 'UT_1Depth_Scaled', 'UT_1_Temp']

out_data = {"time":np.array([])}
for key in canonical_keys:
    out_data[key] = np.array([])

print("Iterating over {} days".format(len(tables)))

for i, day in tqdm(enumerate(tables)):
    cursor.execute("select time,data from {} where device like 'Water_PLC'".format(day))

    temp_dat = {"time":[]}
    for key in canonical_keys:
        temp_dat[key] = []

    cursort = list(sorted(cursor, key=lambda x:x[0].timestamp()))

    for x in cursort:
        temp_dat["time"].append(x[0].timestamp())
        should_be = len(temp_dat["time"])
        for key in canonical_keys:

            if key in x[1]:
                temp_dat[key].append(float(x[1][key]))
            else:
                # if the value isn't updated here, we duplicate it to keep variable lengths consistent
                if len(temp_dat[key])!=0:
                    temp_dat[key].append(temp_dat[key][-1] )
                else:
                    temp_dat[key].append( np.nan )
    for key in out_data:
        out_data[key] = np.concatenate((out_data[key], sample(np.array(temp_dat[key]), 3)))


print("Writing Water Data")
_out_fname = os.path.join(
    os.path.dirname(__file__),
    "water.h5"
)
dfile = h5.File(_out_fname, 'w')
for key in out_data:
    dfile.create_dataset(key, data=out_data[key])
dfile.close()