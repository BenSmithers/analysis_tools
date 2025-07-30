import ROOT
import numpy as np
import uproot
import awkward as ak
import gc
import tracemalloc
import argparse
import os
import time
import json
from analysis_tools import CalibrationDBInterface
from analysis_tools import PMTMapping
from enum import Flag, auto

class HitMask(Flag):
    STABLE_CHANNEL = 0    
    NO_TIMING_CONSTANT = 1 
    SLOW_CONTROL_EXCLUDED = 2 
    
def get_stable_mpmt_list_slow_control(run_number):

    json_path = '/eos/experiment/wcte/configuration/slow_control_summary/good_run_list.json'

    with open(json_path, 'r') as f:
        data = json.load(f)

    run_key = str(run_number)
    print("run_number",run_number)
    if run_key not in data:
        raise ValueError(f"Run number {run_number} not found in the JSON data.")

    enabled_channels = set(data[run_key]["enabled_channels"])
    channel_mask = set(data[run_key]["channel_mask"])

    return enabled_channels, channel_mask

    

def process_data(input_file_names, run_number ,output_dir, timing_offsets_dict, timing_constant_set, slow_control_stable_channels_set):
    # get the timing constants from calibration database

    # make a fast lookup table for the offsets
    # Define a safe lookup function with default fallback
    DEFAULT_OFFSET = 0
    def safe_lookup(glb_pmt_pos_id):
        return timing_offsets_dict.get(glb_pmt_pos_id, DEFAULT_OFFSET)
    timing_offset_lookup = np.frompyfunc(safe_lookup, 1, 1)

    # Vectorized check whether a constant was found function
    def get_hit_mask_vectorized(card_ids: np.ndarray,
                            glb_pmt_pos_id: np.ndarray,
                            timing_constant_set: set,
                            slow_control_stable_channels_set: set) -> np.ndarray:
        """
        Vectorized computation of HitMask flags for arrays of hits.

        Parameters:
            card_ids (np.ndarray): Array of card IDs.
            glb_pmt_pos_id (np.ndarray): Array of global channel position IDs (100*slot + pmt).
            timing_constant_set (set[int]): Channels with timing constants.
            slow_control_stable_channels_set (set[int]): Channels marked stable by slow control.
        Returns:
            np.ndarray: Array of HitMask integer values.
        """
        # Start with STABLE_CHANNEL (0)
        mask = np.full(card_ids.shape, HitMask.STABLE_CHANNEL.value, dtype=np.uint8)

        # Only consider channels with card_id <= 120 (exclude trigger mainboard)
        is_data_channel = card_ids <= 120

        # Channels without timing constants
        no_timing = is_data_channel & ~np.isin(glb_pmt_pos_id, timing_constant_set)
        mask[no_timing] |= HitMask.NO_TIMING_CONSTANT.value

        # Channels excluded by slow control
        not_stable = is_data_channel & ~np.isin(glb_pmt_pos_id, slow_control_stable_channels_set)
        mask[not_stable] |= HitMask.SLOW_CONTROL_EXCLUDED.value

    return mask

    
    tree_name = "WCTEReadoutWindows"  # Replace with actual TTree name

    for input_file_name in input_file_names:
        # Construct output path
        filename = os.path.basename(input_file_name)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, filename)

        input_file = ROOT.TFile.Open(input_file_name)
        tree = input_file.Get(tree_name)
        
        output_file = ROOT.TFile(output_file, "RECREATE")
        out_tree = tree.CloneTree(0)  # clone structure only, no entries

        hit_pmt_calibrated_times = ROOT.std.vector('double')()
        hit_pmt_calibrated_times_branch = out_tree.Branch("hit_pmt_calibrated_times", hit_pmt_calibrated_times)

        hit_pmt_readout_mask = ROOT.std.vector('int')()
        hit_pmt_readout_mask_branch = out_tree.Branch("hit_pmt_readout_mask", hit_pmt_readout_mask)

        for i, entry in enumerate(tree):
            hit_pmt_calibrated_times.clear()
            hit_pmt_readout_mask.clear()

            if i%10_000==0:
                print("On event",i)

            hit_times = np.array(list(entry.hit_pmt_times))
            hit_mpmt_slot = np.array(list(entry.hit_mpmt_slot_ids))
            hit_pmt_pos = np.array(list(entry.hit_pmt_position_ids))
            glb_pmt_pos_id = hit_mpmt_slot * 100 + hit_pmt_pos
            
            timing_offsets = timing_offset_lookup(glb_pmt_pos_id)
            calibrated_times = hit_times - timing_offsets
            
            readout_mask = get_hit_mask_vectorized(card_ids, glb_pmt_pos_id, timing_constant_set, slow_control_stable_channels)
            
            for time, mask in zip(calibrated_times, readout_mask):
                hit_pmt_calibrated_times.push_back(float(time))
                hit_pmt_readout_mask.push_back(bool(mask))
            
            out_tree.Fill()

        out_tree.Write()
        output_file.Close()
        input_file.Close()

    print(f"Finished writing output to: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a new branch to a ROOT TTree in batches.")
    parser.add_argument("-i","--input_files",nargs='+', help="Path to input ROOT file or files")
    parser.add_argument("-r","--run_number", help="Run Number")
    parser.add_argument("-o","--output_dir", help="Directory to write output file")
    args = parser.parse_args()
    
    #get calibration constants
    calibration_db_interface = CalibrationDBInterface()
    timing_offsets_list = calibration_db_interface.get_calibration_constants(args.run_number, 0, "timing_offsets", 0)
    timing_offsets_dict = {}
    #load into dict
    for offset in timing_offsets_list:
        timing_offsets_dict[offset['glb_pmt_id']]=offset['data']
    #set of all channels with calibration constants 
    timing_constant_set = {offset['glb_pmt_id'] for offset in timing_offsets_list}
    
    #get stable list from slow control
    enabled_channels, channel_mask = get_stable_mpmt_list_slow_control(args.run_number)
    stable_channels_card_chan = enabled_channels - channel_mask
    #map slow control data to the 
    mapping = PMTMapping()
    
    slow_control_stable_channels_set = set() #defined in terms of the slot id and pmt position 
    for ch in stable_channels_card_chan:
        card = ch // 100
        pmt_chan = ch % 100
        slot, pmt_pos = mapping.get_slot_pmt_pos_from_card_pmt_chan(card, pmt_chan)
        slow_control_stable_channels_set.add(100 * slot + pmt_pos)
    
    print("len stable_channels",len(slow_control_stable_channels_set))  
    print("len cal constant channel",len(timing_constant_set))  
    print("Stable channels with no calibration constant",slow_control_stable_channels_set-timing_constant_set)
    print("Unstable channels with calibration constant",timing_constant_set-slow_control_stable_channels_set)
    
    
    start = time.time()
    process_data(args.input_files, args.run_number, args.output_dir,timing_offsets_dict, timing_constant_set, slow_control_stable_channels_set)
    end = time.time()
    print(f"Elapsed time: {end - start:.3f} seconds")
    # add_timing_constants(["/eos/experiment/wcte/data/2025_commissioning/offline_data_vme_match/WCTE_offline_R2370S0_VME2005.root"], 2370, "/afs/cern.ch/user/l/lcook/user_data/test")
