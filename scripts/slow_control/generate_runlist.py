
import os
import psycopg2
from math import log2
import json 
import datetime 

print("Opening MySQL connection to neutsrv2")
mydb = psycopg2.connect(
    host="neutsrv2.triumf.ca",
    user="daq_reader",
    password="reader_HD3Z0GFkxMBr",
    database="daq",
    #port=5432
)

from enum import Flag, auto 
class PMTBitmask(Flag):
    zero = auto()
    one = auto()
    two = auto()
    three = auto()
    four = auto()
    five = auto()
    six = auto()
    seven = auto()
    eight = auto()
    nine = auto()
    ten = auto()
    eleven = auto()
    twelve = auto()
    thirteen = auto()
    fourteen = auto()
    fifteen = auto()
    sixteen = auto()
    seventeen = auto()
    eighteen= auto()
    nineteen = auto()

    

cursor = mydb.cursor()

#cursor.execute("select table_schema, table_name from information_schema.tables")


#cursor.execute("select column_name, data_type, character_maximum_length, column_default, is_nullable from INFORMATION_SCHEMA.COLUMNS where table_name = 'public.monitoring_p2025_03_14';")

names = {}

configurations = {}
config_notes = {} # not really used
config_names = {} # name of the configuration file 
config_exclude = {} # what's excluded 

device_config = {} # we should put the device config number for the mpmt per config file 

enabled_channels = {}
cursor.execute("select config_id, data, name, version from configurations")
for x in cursor:
    config_id = int(x[0])
    configurations[config_id] = []
    config_names[config_id] = x[2] + "_v{}".format(x[3])
    config_exclude[config_id] = []
    device_config[config_id] = {}
    enabled_channels[config_id] = {}
    

    # iterate over the in included devices
    for mpmt in x[1].keys():
        if "ExcludedFromRun" in mpmt:
            print("something is excluded", mpmt, config_id)
            config_exclude[config_id].append(mpmt)
            if config_id in config_notes:
                config_notes[config_id]+=", {}".format(mpmt)
            else:
                config_notes[config_id] = "Excluded {}".format(mpmt)
        
        elif "RBU" in mpmt:
            #configurations[config_id].append( int(mpmt.split("MPMT")[1]))

            device_config[config_id][mpmt] = x[1][mpmt]
            enabled_channels[config_id][mpmt] = []
            continue
        elif mpmt=="MPMT":
            continue
        elif mpmt=="LED":
            continue
        elif "MPMT" in mpmt:
            configurations[config_id].append( int(mpmt.split("MPMT")[1]))

            device_config[config_id][mpmt] = x[1][mpmt]
            enabled_channels[config_id][mpmt] = []

config_info ={}

for cf_id in device_config.keys():
    #print(device_config)
    config_info[config_names[cf_id]] = {}

    config_info[config_names[cf_id]]["device_configs"] = {}
    for mpmt_id in device_config[cf_id].keys():
        #print("select device,version,description,data from device_config where device='{}' and version={}".format(mpmt_id, device_config[cf_id][mpmt_id]))
        cursor.execute("select device,version,description,data from device_config where device='{}'".format(mpmt_id))
        config_info[config_names[cf_id]]["device_configs"][mpmt_id] = {}
        found_one = False 
        for x in cursor:
            # device_config[cf_id][mpmt_id]
            this_version = x[1]
            if int(this_version)!=int(device_config[cf_id][mpmt_id]):
                continue
            else:
                found_one = True 
                data = x[3]
                config_info[config_names[cf_id]]["device_configs"][mpmt_id] = data
                if "PMTsEnabled" in data:
                    enabled_channels[cf_id][mpmt_id] = [int(log2(entry.value)) for entry in PMTBitmask(data["PMTsEnabled"]) ]
            if int(this_version)==int(device_config[cf_id][mpmt_id]):
                break
        if not found_one:
            print("Failed to find config {} for {}, {}".format(device_config[cf_id][mpmt_id],mpmt_id,config_names[cf_id] ))


    config_info[config_names[cf_id]]["meta"] = {
        "config_id":cf_id,
        "enabled_channels":enabled_channels[cf_id],
        "excluded":config_exclude[cf_id],
    }
print("Dumping Config")
_obj = open("configurations.json",'wt')
json.dump(config_info, _obj, indent=4)
_obj.close()
print("Done!")
print()

print(configurations.keys())
print("All run info!")
cursor.execute("select run, subrun, start_time, stop_time, config_id from run_info")
run_data = {}

for x in cursor:
    thisdat = x 
    start = x[2].timestamp() if x[2] is not None else None
    end = x[3].timestamp() if x[3] is not None else None

    config_id = x[4]
            
    quality = "Unknown" if (x[3] is not None and x[2] is not None) else "Crashed"
    run_time = end-start if (x[3] is not None and x[2] is not None) else -1

    quality = "Bad" if run_time<0 else quality 
    notes = ""
    
    all_channels = []

    if config_id not in configurations:
        quality = "Bad"
        notes = "Unknown configuration"
        mpmts = []
        name = "?"
        exclude_this = []
    else:
        mpmts = configurations[config_id]
        if config_id in config_notes:
            notes=config_notes[config_id]
        name = config_names[config_id] 
        exclude_this = config_exclude[config_id] 
        
        for this_mpmt in enabled_channels[config_id]:
            if "RBU" in this_mpmt:
                continue
            mpmt_no = int(this_mpmt.split("MPMT")[1])
            all_channels+= [ mpmt_no*100 + chan for chan in enabled_channels[config_id][this_mpmt] ]

        

    run_data[x[0]]= {
        "trigger_name":name,
        "config_id":config_id,
        "hardware_trigger" : "hardware" in name,
        "start": start,
        "end": end,
        "runtime": run_time,
        "notes":notes,
        "quality":quality ,
        "problems":[],
        "mpmts":mpmts,
        "enabled_channels":all_channels,
    }

import json 
import os 
fname = os.path.join(os.path.dirname(__file__), "run_classification_prelim.json")
_obj = open(fname, 'wt')

json.dump(run_data, _obj, indent=4)
_obj.close()

