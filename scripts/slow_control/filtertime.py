import json 
import numpy as np 
import os 

_obj = open(os.path.join(os.path.dirname(__file__), "run_classification.json"), 'r')
_run_data = json.load(_obj)
_obj.close()

BUFFER = 15 

def get_trigger_mask(_run_number:str, trigger_times:np.ndarray):
    """
       run_number -  a string for the run number
       trigger_time - a vector of trigger times in coarse counters  

       returns a length-2 tuple
            np.ndarray of Bools the same length as trigger time. Entries with "True" should be kept; entries with "False" should be discarded
            a vector of bad mPMTs which should be omitted from the entire run
    """

    

    if isinstance(_run_number, (int, float)):
        run_number = str(run_number)
    else:
        run_number = _run_number

    if run_number not in _run_data:
        return np.zeros(len(trigger_times)).astype(bool), []
    
    else:
        this_data = _run_data[run_number]
    
    very_bad = this_data["runtime"]<600
    if very_bad:
        return np.zeros(len(trigger_times)).astype(bool), this_data["mpmts"]

    bad_mask = np.zeros(len(trigger_times)).astype(bool)
    bad_channel = []
    for problem in this_data["problems"]:
        # adding a 5 second window on either side 
        start   = (problem[0] - this_data["start"] -BUFFER)*(1e9)/8,
        end     = (problem[1] - this_data["start"] +BUFFER)*(1e9)/8,
        prob    = problem[2]
        if "dropped" in prob:
            # filter all trigger times within +/- buffer of the dropped packets 
            bad_mask = np.logical_or(bad_mask, np.logical_and(trigger_times>start, trigger_times<end) )

        elif ("no_data" in prob):
            this_mpmt = int(prob.split(":")[0][4:])
            for i in range(20):
                this_channel = this_mpmt*100 + i
                if this_channel not in bad_channel:
                    bad_channel.append( this_channel )
            
        elif ("Status." in prob):
            this_mpmt = int(prob.split(":")[0][4:])
            this_pmtno = int(prob.split(" ")[1][3:])
            this_channel = this_mpmt*100 + this_pmtno
            if this_channel not in bad_channel:
                bad_channel.append( this_channel )
            
        elif "bad_flow" in prob:
            pass 
        elif "crashed" in prob:
            bad_mask = np.logical_or(bad_mask, trigger_times>(this_data["end"]-30) )
        else:
            print(prob)
            raise ValueError("Unhandled problem!")
    return np.logical_not(bad_mask), bad_channel