import numpy as np 

from enum import Enum, Flag
from scipy.optimize import minimize 
import os 
import json 

class mPMTState(Enum):
    good = 0
    unstable_rates = 1
    unstable_hv = 2
    no_data=3
    water_interrupt = 4

class waterState(Enum):
    good = 0
    bad_flow = 1 
    no_flow = 2
class Status(Flag):
    null = 0
    hv_on = 1 
    hv_present = 2
    under_voltage = 4
    over_voltage = 8
    over_current = 16 
    trip = 32   
    undefined_status = 64

class HVStatus(Enum):
    good = 0
    under_voltage = 1
    over_voltage = 2
    over_current = 3
    trip = 4
    no_data = 5
    undefined_status = 6

class RateState(Enum):
    ok_rate = 0
    no_data = 1
    zero_rate =2

class Packets(Enum):
    none = 0
    dropped = 1

_fname = os.path.join(os.path.dirname(__file__),"run_classification_prelim.json")
_obj = open(_fname, 'r')
_run_data = json.load(_obj)
_obj.close()

def get_bad_windows(times:np.ndarray, bad_mask:np.ndarray, paramter:np.ndarray, which_enum:Enum, label=""):
    """
        times - np array with a timestamp
        bad_mask - an array of booleans. True is bad
        parameter - associated with the measured value 

    Returns
        list of tuples
            (start time, end time, parameter associated with "bad")
    """
    indices = np.arange(len(times))
    steps = np.diff(bad_mask.astype(int))
    ret_vals = []
    if len(steps)!=0:
        starts = indices[np.append(steps, [False,])==1]+1
        ends = indices[np.append([False, ], steps) ==-1]


        for i in range(len(starts)):
            if len(ends)==0:
                these_indices = indices[starts[i]:]
            else:
                if i == len(ends):
                    these_indices = indices[starts[i]: ]
                else:
                    these_indices = indices[starts[i]: ends[i]]

                
            if len(these_indices)==1:
                ret_vals.append( 
                    [times[these_indices[0]], times[these_indices[-1]], label+str(which_enum(int(paramter[these_indices[0]]))) ]
                ) 
            elif len(these_indices)==0:
                pass
            else:
                ret_vals.append( 
                    [times[these_indices[0]], times[these_indices[-1]], label+str(which_enum(int(paramter[these_indices[0]]))) ]
                )
    return ret_vals


def get_all_runs():
    return list(_run_data.keys())

def get_run_meta(run_no):
    if run_no in _run_data:
        return _run_data[run_no]
    else:
        raise KeyError("No known run {}".format(run_no))

def check_water(water_dict):
    flows = water_dict["FT1_Flow"]
    times = water_dict["time"]
    flow_state = np.array([waterState.good.value for i in range(len(flows))])
    bad_mask = np.logical_or(flows<1.0, flows==0)
    flow_state[bad_mask] = waterState.bad_flow.value
    
    windows = get_bad_windows(times, bad_mask, flow_state, waterState)
    
    return windows

    
def check_packets(packet_dict):
    times = packet_dict["time"]
    dropped = packet_dict["drop"]
    dropped = np.concatenate(([0,], np.diff(dropped)))

    bad_mask = dropped>0 
    packet_state = np.zeros(len(dropped))
    packet_state[bad_mask] = 1

    windows = get_bad_windows(times, bad_mask, packet_state, Packets)
    return windows

def check_status(status_dict):
    if len(status_dict["time"])<3:
        return [ [np.nan, np.nan,str(HVStatus.no_data)], ]

    windows = []
    for key in status_dict.keys():
        if key=="time":
            continue
        status_dict[key][np.isnan(status_dict[key])] = 64
        statuses = np.array([int(entry) for entry in status_dict[key]])
        bad_mask = statuses!=3

        pre_filter = statuses!=0 
        
        windows += get_bad_windows(status_dict["time"][pre_filter], bad_mask[pre_filter], statuses[pre_filter], Status, label=key)

    return windows

def check_rates(rate_dict:dict):
    if len(rate_dict["time"])<3:
        return [ [np.nan, np.nan,str(RateState.no_data)], ]

    windows = []
    for key in rate_dict.keys():
        if "time"==key:
            continue
        this_data = rate_dict[key]
        bad_mask = this_data == 0
        if len(this_data[bad_mask])>0 and len(this_data[bad_mask])!=len(this_data):
            statuses = np.zeros(len(this_data))
            statuses[bad_mask] = 2
            windows += get_bad_windows(rate_dict["time"], bad_mask, statuses, Status, label=key)

    return windows

def check_hv(rate_dict:dict):
    """
        should be the standard...
        expects dictionary in time and pmt 
    """
    if len(rate_dict["time"])<3:
        return mPMTState.no_data
    times = np.array(rate_dict["time"]) - np.min(rate_dict["time"])
    
    for key in rate_dict.keys():

        yvals = rate_dict[key]
        # may want to use this mask...
        mask = np.logical_and(yvals>0.001, yvals<4 )
        if np.sum(mask)==0:
            continue

        try:
            slope, yint = np.polyfit(times[mask], yvals[mask], deg=1)
            if slope > 2.78e-05: # 200mV in 3 hours 
                return mPMTState.unstable_hv
        except np.linalg.LinAlgError:
            return mPMTState.unstable_hv 

    return mPMTState.good 
