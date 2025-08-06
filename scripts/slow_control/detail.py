"""
    Pulls the data for a run and plots it in high detail 
"""

import os 
import matplotlib.pyplot as plt 
import json 
from datetime import datetime 
import numpy as np 
import mysql.connector


def get_color(n, colormax=3.0, cmap="viridis"):
    this_cmap = plt.get_cmap(cmap)
    return this_cmap(n/colormax)

_fname = os.path.join(os.path.dirname(__file__),"run_classification_prelim.json")
_obj = open(_fname, 'r')
_run_data = json.load(_obj)
_obj.close()

def get_run_meta(run_no):
    if run_no in _run_data:
        return _run_data[run_no]
    else:
        raise KeyError("No known run {}".format(run_no))


def return_detail(run_no,mpmt, table_template, qty_template, window:float, format=True)->dict:
    mydb = mysql.connector.connect(
        host="neutsrv2.triumf.ca",
        user="history_reader",
        password="reader_PsFtKL5kR3",
        database="history"
    )

    cursor = mydb.cursor()

    out_data = {}

    table = table_template + "{:03d}".format(mpmt)

    all_quantities = ",".join([qty_template.format(mpmt, i) for i in range(19)]) 
    all_quantities = "_i_time,"+all_quantities
    keys = ["time"] + ["pmt{}".format(i) for i in range(19)] 

    run_data = get_run_meta(str(run_no))
    

    tmax = run_data["end"]
    tmin = run_data["start"]
    if window!=0.0:
        slope = (tmax - tmin)/100 

        tmin = window * slope + tmin  
        tmax = tmin + 300 


    data = []
    command = "select {} from {} where _i_time > {} and _i_time <{}".format(all_quantities, table, tmin, tmax)
    cursor.execute(command) 
    for x in cursor:
        data.append(np.array(x, dtype=float))

    data = np.transpose(data)

    for i,subkey in enumerate(keys):
        data[i][np.isnan(data[i])] = np.nan
        out_data[subkey] = data[i]

    return out_data

def plot_data_mPMT(data:dict, run_no:int,mpmt:int, title:str):
    times = np.array([datetime.fromtimestamp(entry +9*3600) for entry in data["time"]])
    if len(times)==0:
        return 
    
    for i in range(19):
        n_above = (data["pmt{}".format(i)] - np.mean(data["pmt{}".format(i)]))>0.1

        plt.plot(times, data["pmt{}".format(i)],label="PMT {}".format(i), color=get_color(i, 20), ls='-', marker='.', alpha=0.3)

        # fraction 0.1 above mean 
        
        
        print(run_no, mpmt, i, np.sum(n_above)/len(data["pmt{}".format(i)]) )
    plt.xlabel("Time")
    plt.title("Run {}; {};".format(run_no,times[0]))
    plt.ylabel(title)
    #plt.yscale('log')
    plt.gcf().autofmt_xdate()
    plt.savefig("./detail_plots/{}_m{}_{}.png".format(title,mpmt,run_no),dpi=400)
    plt.clf()

if __name__=="__main__":

    ### PARSE USER INPUT
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--run",type=int,
                    help="The run to investigate")
    parser.add_argument("--mpmt",type=int,
                    help="The mPMT to investigate")
    parser.add_argument("--window",type=int,default=0.0,
                    help="Percent (0-100) through run to focus on")
    parser.add_argument("--hv", default=False, action="store_true",
                    help="Plot HV")
    parser.add_argument("--rates", default=False, action="store_true",
                    help="Plot rates")
    parser.add_argument("--status", default=False, action="store_true",
                    help="Plot status")

    options = parser.parse_args()
    run = options.run
    mpmt = options.mpmt
    hv = options.hv
    rates = options.rates
    status = options.status
    window = options.window

    if hv:
        data=return_detail(run,mpmt,"mpmtmon_i", "m{:03d}_pmt{}_hvcurval", window)
        plot_data_mPMT(data, run, mpmt, "HV")
    if rates:
        return_detail(run,mpmt, "mpmtmon_h", "m{:03d}_pmt{}_hit_cnt_rate",window)
    if status:
        data = return_detail(run,mpmt,"mpmtmon_s", "m{:03d}_pmt{}_status1", window)
        plot_data_mPMT(data, run, mpmt, "status")

