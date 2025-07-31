import json
from importlib.resources import files

class PMTMapping:
    def __init__(self):
        # Load the JSON from the package's data folder
        json_path = files('analysis_tools.data').joinpath('PMT_Mapping.json')
        print("json path",json_path)
        with json_path.open('r') as file:
            self.pmt_data = json.load(file)["mapping"]

    def get_positions_from_entry(self,long_form_id):
        # longform ID is mpmt_id * 100 + pmt_id
        return long_form_id // 100, long_form_id % 100

    def get_key_from_value(self, input_value):
        for key, value in self.pmt_data.items():
            if value == input_value:
                return key
        return None  # No match found
    
    def get_slot_pmt_pos_from_card_pmt_chan(self,card_id,pmt_channel):
        if str((100*card_id)+pmt_channel) in self.pmt_data:
            slot_id, pmt_pos = self.get_positions_from_entry(self.pmt_data[str((100*card_id)+pmt_channel)])
        else:
            raise Exception("Card chan",card_id,pmt_channel,"not in mapping json")
        return slot_id, pmt_pos
    
    def get_card_pmt_chan_from_slot_pmt_pos(self,slot_id, pmt_pos):
        value = ((100*slot_id)+pmt_pos)
        key = self.get_key_from_value(value)
        if key is None:
            raise Exception("No card, chan found for slot",slot_id,"pmt pos",pmt_pos)
        key = int(key)
        return self.get_positions_from_entry(key)