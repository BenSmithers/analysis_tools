
import os
from time import time
import mysql.connector

import numpy as np 
import h5py as h5
from tqdm import tqdm 

"""
    Pre-caches all of the slow control data from the midas database
"""


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

def extract(table_template:str, qty_template:str, outname:str, format=True):
    print("Opening MySQL connection to neutsrv2")
    mydb = mysql.connector.connect(
        host="neutsrv2.triumf.ca",
        user="history_reader",
        password="reader_PsFtKL5kR3",
        database="history"
    )

    cursor = mydb.cursor()

    # mpmtmon_i027
    # 1 - mpmtmon_i132
    tables = []
    cursor.execute("SHOW TABLES")
    for x in cursor:
        tables.append( x[0] )

    tables = list(filter(lambda x:table_template in x, tables))

    out_data = {}

    outfile = h5.File(outname, 'w')

    tmin = 1735736461
    tmax = 1750698787

    for table in tqdm(tables):
        pmt_id = table.split(table_template)[-1] 
        

        if format:
            all_quantities = ",".join([qty_template.format(pmt_id, i) for i in range(20)]) 
            all_quantities = "_i_time,"+all_quantities
            keys = ["time"] + ["pmt{}".format(i) for i in range(20)] 
        else:
            all_quantities = "_i_time,"+qty_template.format(pmt_id)
            keys = ["time", qty_template.format(pmt_id)]
            
        
        command = "select {} from {} where _i_time > {} and _i_time <{}".format(all_quantities, table, tmin, tmax)
        data = []

        cursor.execute(command) 
        for x in cursor:
            data.append(np.array(x, dtype=float))
        
        data = np.transpose(data)

        out_data[table] = {}
        for i,subkey in enumerate(keys):
            data[i][np.isnan(data[i])] = np.nan
            if format:
                out_data[table][subkey] = sample(data[i], 10)
            else:
                out_data[table][subkey] = data[i]
            try:
                outfile.create_dataset("{}/{}".format(table, subkey), data=out_data[table][subkey])
            except TypeError:
                print("Trouble with {}/{}".format(table, subkey))
                continue

    outfile.close()

if __name__=="__main__":
    hvfile =os.path.join(os.path.dirname(__file__),"data_cache","hv_out.h5")
    hrfile =os.path.join(os.path.dirname(__file__),"data_cache","rate_out.h5")
    state_file =os.path.join(os.path.dirname(__file__),"data_cache","state_out.h5")
    drop_file =os.path.join(os.path.dirname(__file__),"data_cache","drop_file.h5")
    
    if not os.path.exists(hvfile):
        extract("mpmtmon_i", "m{}_pmt{}_hvcurval", hvfile)
    else:
        print("skipping hv")
    if not os.path.exists(hrfile):
        extract("mpmtmon_h", "m{}_pmt{}_hit_cnt_rate", hrfile)
    else:
        print("skipping hr")
    if not os.path.exists(drop_file):
        extract("mpmtmon_x", "m{}_last_run_frames_dropped", drop_file, False)
    else:
        print("skipping dropped")
    if not os.path.exists(state_file):
        extract("mpmtmon_s", "m{}_pmt{}_status1", state_file)
    else:
        print("skipping status")

