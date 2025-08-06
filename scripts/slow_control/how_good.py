import json 
import numpy as np

import os 
from filtertime import get_trigger_mask
import matplotlib.pyplot as plt 


_obj = open(
    os.path.join(
        os.path.dirname(__file__),
        "run_classification.json"
    ), 'r'
)

data = json.load(_obj)
_obj.close()

good_minutes = 0
bad_minutes = 0
total_minutes = 0

good_runs = 0
caution = 0
bad_runs = 0

key_list = data.keys()
filter_keys = []

f_bins = np.linspace(0, 1, 101)
live_bins = np.linspace(0, 240, 100)
chan_bin = np.linspace(0, 1000, 100)
nbad = []
livetime = []
f_obs = []
for key in key_list:

    if int(key)<1354:
        filter_keys.append(key)
        continue

    this_dict = data[key]
    rt =  this_dict["runtime"]
    

    if rt<0:
        filter_keys.append(key)
        continue # nonsense 

    if False : # "Bad" in this_dict["quality"]:
        bad_minutes+= rt
        total_minutes+= rt
        print("Run", key, "0% good; 100% bad")
        bad_minutes+=1 
        filter_keys.append(key)
        continue


    water = False
    for prob in this_dict["problems"]:
        if "water" in prob[2]:
            water = True 
            break 
        
    crash = False
    for prob in this_dict["problems"]:
        tweak_end = -1 
        if "crash" in prob[2]:
            crash = True 
            # now, get the adjusted end time ... 
            for subprob in this_dict["problems"]:
                if "drop" in subprob[2]:
                    tweak_end = subprob[0] 
                    break
            break 
    if crash and (tweak_end!=-1):
        this_dict["runtime"] = tweak_end - this_dict["start"]
        this_dict["end"] = tweak_end
        rt = this_dict["runtime"]
        this_dict["notes"] += "Set end time to the first dropped packet problem entry"

    these_times = np.linspace(
        this_dict["start"],
        this_dict["end"],
        int(rt)
    ) 

    
    these_times -= these_times.min()
    these_times*=(1e9)/8

    tmask, channel_mask = get_trigger_mask(key, these_times)

    fraction = len(channel_mask)/(len(this_dict["mpmts"])*19)

    good_minutes +=rt*np.sum(tmask)/len(tmask)
    this_dict["effective_runtime"] = rt*np.sum(tmask)/len(tmask)
    bad_minutes += rt*(1- (np.sum(tmask)/len(tmask)))
    total_minutes += rt 

    print("Run", key, "{}% good; {}% bad".format(
        100*np.sum(tmask)/len(tmask), 100*(1-np.sum(tmask)/len(tmask))
    ))

    nbad.append(len(channel_mask))
    
    if this_dict["effective_runtime"]<(30*60):
        this_dict["notes"]+="Short run. "

    f_obs.append(np.sum(tmask)/len(tmask))
    livetime.append(this_dict["effective_runtime"]/60)
    if water:
        this_dict["notes"] = "water flow issues"
    if (np.sum(tmask)/len(tmask))>0.90 and (not water) and this_dict["effective_runtime"]>(30*60) and (not crash) and (len(channel_mask)==0):
        good_runs+=1 
        this_dict["quality"] = "good"
    elif this_dict["effective_runtime"]>(10*60) and (np.sum(tmask)/len(tmask))>0.10 and (len(channel_mask)<100):
        this_dict["quality"] = "caution"
        caution+=1
    else: # short run time  
        bad_runs+=1
        this_dict["quality"] = "bad"
        filter_keys.append(key)

    this_dict["channel_mask"] = channel_mask

fractional_hist = np.histogram(f_obs, f_bins)[0]
plt.stairs(fractional_hist, f_bins)
plt.xlabel("Fraction Live",size=14)
plt.ylabel("Counts",size=14)
plt.yscale('log')
plt.savefig("./plots/fraction_live.png",dpi=400)

plt.clf()

livetime_hist = np.histogram(livetime,live_bins)[0]
plt.stairs(livetime_hist, live_bins)
plt.xlabel("Eff. Livetime [min]",size=14)
plt.ylabel("Counts",size=14)
plt.yscale('log')
plt.savefig("./plots/livetime_live.png",dpi=400)

plt.clf()

chan_hist = np.histogram(nbad,chan_bin)[0]
plt.stairs(chan_hist, chan_bin)
plt.xlabel("Bad Channels",size=14)
plt.ylabel("Counts",size=14)
plt.yscale('log')
plt.savefig("./plots/chan_bad.png",dpi=400)


for key in filter_keys:
    if key in data:
        del data[key]
    
print("Total")
print("    {} minutes good".format(good_minutes/60))
print("    {} minutes bad".format(bad_minutes/60))

print("{} Good Runs".format(good_runs))
print("{} Caution Runs".format(caution))
print("{} Bad Runs".format(bad_runs))

_obj = open(
    os.path.join(
        os.path.dirname(__file__),
        "good_run_list.json"
    ), 'w'
)

json.dump(data,_obj, indent=4)
_obj.close()


