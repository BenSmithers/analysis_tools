First, 

Run `water_extractor.py` and the `extractor.py` to pre-cache the slow control data files. 
You may also need to create the `data_cache`, `plots`, and `detail_plots` folders within the `slow_control` folder. 
These can take a while to run. 

From then, run `generate_runlist.py` to prepare the preliminary runlist. 

You should then be able to run `classify_runs.py` to identify all problematic periods. 
This can take a while. 

Finally, `how_good.py` can be used to generate the good run list. 