import json
import os 

from check_code import get_run_meta, check_hv, get_all_runs, check_water, check_status, check_rates, check_packets
from reader import get_hv, get_state, get_rate, get_water, get_drop
from detail import plot_data_mPMT, return_detail
from plot_run import plot_water 
from tqdm import tqdm
from enum import Enum, Flag 
import numpy as np 

"""
    Runs over the preliminary run list and identifies problems
"""

class RunFlag(Flag):
    Good = 0
    Caution = 1
    Bad = 2

def check_run(run_no):
    run_data = get_run_meta(run_no)
    start = -1
    end = -1
    if run_data["end"] is None:
        run_data["quality"] = RunFlag.Caution 
        start = run_data["start"]
        
        try:
            run_data["end"] = get_run_meta(str(int(run_no)+1))["start"]
            
        except:
            end = -1
            run_data["quality"] = RunFlag.Bad | RunFlag.Caution
            run_data["quality"] = str(run_data["quality"])
            return run_data
        end = run_data["end"]
        run_data["runtime"] = end - start
        run_data["problems"].append([0, 0, "Run crashed, using next run start as end"])
    elif run_data["quality"]=="Bad":
        run_data["quality"] = RunFlag.Bad | RunFlag.Caution
        run_data["quality"] = str(run_data["quality"])
        return run_data
                
    else:
        start = run_data["start"]
        end = run_data["end"]

    

    # enabled mPMTs
    mpmts = np.unique( np.array(run_data["enabled_channels"]) //100)

    notes = run_data["notes"]
    if len(mpmts)==3 or len(mpmts)==4:
        if 130 in mpmts and 131 in mpmts and 132 in mpmts:
            run_data["quality"] = RunFlag.Caution
            run_data["quality"] = str(run_data["quality"])
            return run_data
    if run_data["runtime"]<60:
        run_data["quality"] =  RunFlag.Bad 
        run_data["quality"] = str(run_data["quality"])
        run_data["notes"] += "Too short. "
        return run_data

    run_data["quality"] = RunFlag.Good
    water_state = check_water(get_water(start, end))


    for entry in water_state:
        run_data["problems"].append( entry )
    if len(water_state)!=0:
        plot_water(run_no)
        run_data["quality"] =  RunFlag.Caution | run_data["quality"] 




    one_too_short = False
    for mpmt in mpmts:
        packet_state = check_packets(get_drop(mpmt, start, end))
        for entry in packet_state:
            entry[-1] = "mpmt{}: ".format(mpmt) + entry[-1]
            run_data["problems"].append(entry)
            run_data["quality"] = RunFlag.Caution | run_data["quality"] 
        is_trigger = (mpmt == 130) or (mpmt == 131) or (mpmt == 132)
        #rates = get_hv(mpmt, start, end)
        these_rates = check_rates(get_rate(mpmt, start, end))
        for entry in these_rates:
            entry[-1]="mpmt{}: ".format(mpmt) + entry[-1]
            run_data["problems"].append(entry)
            run_data["quality"] =  RunFlag.Bad | run_data["quality"] 

        these_states = check_status(get_state(mpmt, start, end))
        for entry in these_states:
            entry[-1]="mpmt{}: ".format(mpmt) + entry[-1]
            run_data["problems"].append(entry)
            run_data["quality"] =  RunFlag.Bad | run_data["quality"] 

        #result =check_hv(rates)

    if one_too_short:
        run_data["notes"] += "HV data missing. "
    run_data["quality"] = str(run_data["quality"])
    return run_data

if __name__=="__main__":
    run_data = {}
    i=0
    for rno in tqdm(get_all_runs()):
        i+=1

        if i<1130:
            continue
        if i>3000:
            break

        #print(rno)
        run_data[rno] = check_run(rno)
    
    _fname = os.path.join(os.path.dirname(__file__), "run_classification.json")
    _obj = open(_fname ,'w')
    json.dump(run_data, _obj, indent=4)
    _obj.close()
