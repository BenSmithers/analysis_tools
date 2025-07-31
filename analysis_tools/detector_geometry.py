import json
import os
import numpy as np

class DetectorGeometry:
    def __init__(self):
        # blacksheet to blacksheet distance in mm
        self.diameter = 3075.926 
        self.height = 2714.235

        self.json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/wcte_v11_20250513.json")

        # load mPMT positions, directions and types
        with open(self.json_file) as json_data:
            mPMT_config = json.load(json_data)

        self.mpmts = 106
        self.pmts = 19

        self.mpmts_type = np.zeros(self.mpmts,dtype=np.byte) # 1 = in-situ, 2 = ex-situ, 3 = FD

        self.mpmts_pos = np.empty((self.mpmts,self.pmts,3))
        self.mpmts_dir = np.empty((self.mpmts,self.pmts,3))

        for i in range(self.mpmts):

            mpmt_type = mPMT_config["mpmt_type"][i]
            if mpmt_type == "In-situ":
                self.mpmts_type[i] = 1
            elif mpmt_type == "Ex-situ":
                self.mpmts_type[i] = 2
            elif mpmt_type == "FD":
                self.mpmts_type[i] = 3

            for j in range(self.pmts):
                for k in range(3):
                    self.mpmts_pos[i][j][k] = mPMT_config["mpmts"]["%i" % i]["pmts"]["%i" % j]["placement"]["location"][k]
                    self.mpmts_dir[i][j][k] = mPMT_config["mpmts"]["%i" % i]["pmts"]["%i" % j]["placement"]["direction_z"][k]

    def calc_tof(self, pos):
        c_over_n = 3.e8 * 1000 / 1e9 / 1.33  # mm/ns
        # Convert pos to array if not already
        pos = np.asarray(pos)
        # Compute (pos - mpmts_pos) ** 2 along last axis
        diff = pos - self.mpmts_pos  # shape (mpmts, pmts, 3)
        dist2 = np.sum(diff ** 2, axis=2)  # shape (mpmts, pmts)
        tof = np.sqrt(dist2) / c_over_n
        return tof