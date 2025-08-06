import numpy as np
import json 
import sys 
import h5py as h5 
import os 

from reader import get_hv, get_state, get_rate, get_water, get_drop
import matplotlib.pyplot as plt 
from datetime import datetime

from check_code import get_run_meta

def get_color(n, colormax=3.0, cmap="viridis"):
    this_cmap = plt.get_cmap(cmap)
    return this_cmap(n/colormax)


def plot_water(run_no):
    run_data = get_run_meta(run_no)
    start = run_data["start"]
    end = run_data["end"]
    water_data = get_water(start, end)

    times = np.array([datetime.fromtimestamp(entry+9*3600) for entry in water_data["time"]])
    if len(times)>0:
        plt.plot(times, water_data["FT1_Flow"], color=get_color(10, 20), marker='.', ls='')
        print(np.mean(water_data["FT1_Flow"]),np.std(water_data["FT1_Flow"]))

        plt.title("Run {}; {}".format(run_no,times[0]))
        plt.xlabel("Time")
        plt.ylabel("Flow")
        plt.ylim([0, 3])
        plt.gcf().autofmt_xdate()
        plt.savefig("./plots/water_flow_{}.png".format(run_no),dpi=400)
        plt.clf()
    else:
        print("No Watermon data for {}".format(run_no))
        

def main(run_no):
    run_data = get_run_meta(run_no)
    if run_data["quality"]=="Bad" or run_data["quality"]=="Crashed":
        print("Skipping bad run")
        return 
    
    start = run_data["start"]
    end = run_data["end"]

    mpmt_no = 101

    rates = get_rate(mpmt_no, start, end)
    hvs = get_hv(mpmt_no, start, end)
    states = get_state(mpmt_no, start, end)
    water_data = get_water(start, end)
    drop = get_drop(mpmt_no, start, end)
    from check_code import check_hv
    print(check_hv(hvs))

    times = np.array([datetime.fromtimestamp(entry +9*3600) for entry in drop["time"]])
    if len(times)>0:
        plt.plot(times, drop["drop"], ls='', marker='.')
        plt.xlabel("Time")
        plt.title("Run {}; {}".format(run_no,times[0]))
        plt.ylabel("Dropped Packets")
        if np.max(drop["drop"])<1:
            plt.ylim([-1, 10])
        else:
            plt.ylim([0,1.2*np.max(drop["drop"])])
        plt.gcf().autofmt_xdate()
        plt.savefig("./plots/drop_m{}_{}.png".format(mpmt_no,run_no),dpi=400)
        plt.clf() 
    else:
        print("no dropped packets data")

    times = np.array([datetime.fromtimestamp(entry +9*3600) for entry in rates["time"]])
    if len(times)>0:
        for i in range(19):
            plt.plot(times, rates["pmt{}".format(i)],label="PMT {}".format(i), color=get_color(i, 20))
        plt.xlabel("Time")
        plt.title("Run {}; {}".format(run_no,times[0]))
        plt.ylabel("Rates")
        plt.yscale('log')
        plt.gcf().autofmt_xdate()
        plt.savefig("./plots/rates_m{}_{}.png".format(mpmt_no,run_no),dpi=400)
        plt.clf()
    else:
        print("No Rate Data")

    times = np.array([datetime.fromtimestamp(entry+9*3600) for entry in hvs["time"]])
    if len(times)>0:
        for i in range(19):
            submask = hvs["pmt{}".format(i)]!=0
            plt.plot(times[submask], hvs["pmt{}".format(i)][submask],label="PMT {}".format(i), color=get_color(i, 20))
            #print("")
        plt.xlabel("Time")
        plt.title("Run {}; {}".format(run_no,times[0]))
        plt.ylabel("HV")
        plt.gcf().autofmt_xdate()
        plt.ylim([0.5, 1.7])

        plt.savefig("./plots/hvs_m{}_{}.png".format(mpmt_no,run_no),dpi=400)
        plt.clf()
    else:
        print("No HV data")

    times = np.array([datetime.fromtimestamp(entry+9*3600) for entry in states["time"]])
    if len(times)>0:
        for i in range(19):
            plt.plot(times, states["pmt{}".format(i)],label="PMT {}".format(i), color=get_color(i, 20))
        plt.title("Run {}; {}".format(run_no,times[0]))
        plt.xlabel("Time")
        plt.ylabel("States")
        plt.gcf().autofmt_xdate()
        plt.savefig("./plots/states_m{}_{}.png".format(mpmt_no,run_no),dpi=400)
        plt.clf()
    else:
        print("No State Info")

    times = np.array([datetime.fromtimestamp(entry+9*3600) for entry in water_data["time"]])
    if len(times)>0:
        plt.plot(times, water_data["FT1_Flow"], color=get_color(10, 20), marker='.', ls='')
        print(np.mean(water_data["FT1_Flow"]),np.std(water_data["FT1_Flow"]))

        plt.title("Run {}; {}".format(run_no,times[0]))
        plt.xlabel("Time")
        plt.ylabel("Flow")
        plt.ylim([0, 3])
        plt.gcf().autofmt_xdate()
        plt.savefig("./plots/water_flow_{}.png".format(run_no),dpi=400)
        plt.clf()
        

if __name__=="__main__":
    assert len(sys.argv)==2, "Must pass only run number"

    main(sys.argv[1])