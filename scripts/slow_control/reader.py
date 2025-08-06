import h5py as h5
import os 
import numpy as np 

hvfile =h5.File( os.path.join(os.path.dirname(__file__),"data_cache","hv_out.h5"),'r')
hrfile =h5.File(os.path.join(os.path.dirname(__file__),"data_cache","rate_out.h5"), 'r')
state_file =h5.File(os.path.join(os.path.dirname(__file__),"data_cache","state_out.h5"), 'r')
drop_file =h5.File(os.path.join(os.path.dirname(__file__),"data_cache","drop_file.h5"),'r')
water = h5.File(os.path.join(os.path.dirname(__file__), "data_cache","water.h5"), 'r')

def get_drop(mpmt, start, end):
    this_table = drop_file["mpmtmon_{}{:03d}".format("x",mpmt)] 
    times = np.array(this_table["time"])
    mask = np.logical_and( times>start, times<end+120)

    return {
        "time": times[mask],
        "drop": this_table["m{:03d}_last_run_frames_dropped".format(mpmt)][mask]
    }

def get_hv(mpmt, start, end):
    return __get(hvfile, mpmt, start, end, letter="i")
def get_state(mpmt, start, end):
    return __get(state_file, mpmt, start, end, letter="s")
def get_rate(mpmt, start, end):
    return __get(hrfile, mpmt, start, end, letter="h")
def get_water(start, end):
    times = np.array(water["time"])

    mask = np.logical_and(times>start, times<end)
    return {
        key: water[key][mask] for key in water.keys()
    }

def __get(what, mpmt, start, end, letter):
    this_table = what["mpmtmon_{}{:03d}".format(letter,mpmt)]

    times = np.array(this_table["time"])

    mask = np.logical_and( times>start, times<end)

    return {
        key:this_table[key][mask] for key in this_table.keys()
    }


