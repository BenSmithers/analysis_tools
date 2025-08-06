from time import time
import psycopg2
import numpy as np 
from tqdm import tqdm 
import os 
import h5py as h5 


def sample(thisdat, group=10):
    """
        Sample 1 of every GROUP in $thisdat
    """
    if group==1:
        return thisdat 
    mask = np.arange(len(thisdat)) % group == 0
    return thisdat[mask]


print("Opening MySQL connection to neutsrv2")
mydb = psycopg2.connect(
    host="neutsrv2.triumf.ca",
    user="daq_reader",
    password="reader_HD3Z0GFkxMBr",
    database="daq",
    #port=5432
)

cursor = mydb.cursor()


tables = []
cursor.execute("select table_schema, table_name from information_schema.tables")
for x in cursor:
    if "monitoring" in x[1] and ("1970" not in x[1]) and ("default" not in x[1]):
        tables.append(x[1])
tables = list(sorted(tables))
print("Processing...", tables[:5])

canonical_keys = ["pmt{}_hvvolval".format(i) for i in range(19)]
canonical_keys += ["pmt{}_hvvolnom".format(i) for i in range(19)]

out_data = {}
did_one = False

for i, day in enumerate(tables):
    # we need to get the table names then 
    if day=="monitoring":
        continue
    if "p2024" in day:
        continue
    print("select device from {}".format(day))
    cursor.execute("select device from {}".format(day))
    temp_data = {}
    
    for x in cursor: # iterate over all the tables, build a dict of unique IDs 
        mpmt_key = str(x[0])
        if "MPMT" not in mpmt_key:
            pass
        elif "130" in mpmt_key or "131" in mpmt_key or "132" in mpmt_key:
            pass
        elif mpmt_key not in temp_data:
            did_one = True
            temp_data[mpmt_key] = {subkey:[] for subkey in canonical_keys}
            temp_data[mpmt_key]["time"] = []  

    for key in temp_data: # iterate over the mpmts
        print("    select time,data from {} where device like '{}'".format(day, key))
        cursor.execute("select time,data from {} where device like '{}'".format(day, key))
        for x in cursor:
            temp_data[key]["time"].append(x[0].timestamp())
            data_dict = x[1] 

            for subkey in canonical_keys:
                # for each PMT value, we append the time and value *if it's there*
                if subkey in data_dict:
                    temp_data[key][subkey].append(data_dict[subkey])
                else: # otherwise append NAN
                    temp_data[key][subkey].append(np.nan)
        # add this mpmt data to the out_data
        
        if key not in out_data:
            out_data[key] = {subkey:np.array([]) for subkey in canonical_keys}
            out_data[key]["time"] = np.array([])
        
        for subkey in temp_data[key].keys():
            out_data[key][subkey] = np.concatenate((out_data[key][subkey], sample(np.array(temp_data[key][subkey]), 10)))
    break 
print("there were", len(tables), "days")

print("Writing HV Data")
_out_fname = os.path.join(
    os.path.dirname(__file__),
    "hv_mon2.h5"
)
dfile = h5.File(_out_fname, 'w')
for key in out_data:
    for subkey in out_data[key].keys():
        dfile.create_dataset("{}/{}".format(key, subkey), data=out_data[key][subkey])
dfile.close()