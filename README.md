Installation:

git clone <git repo location>
cd analysis_tools
pip install -e .

The -e flag allows you to edit the package 
If using on lxplus you will need to setup this in a python virtual environment 

##  WaveformProcessing

Waveform processing contains a copy of the CFD used in the test stand repository
WaveformProcessing.cfd_teststand_method() processes the CFD using that method returning 
the charge and the time for a pulse in that waveform - including non-linearity corrections 
for both

## do_pulse_finding and do_pulse_finding_vect

Finds pulses in the waveforms using the same method as run online on the mPMT. do_pulse_finding_vect is
a vectorised version

## CalibrationDBInterface

Interfaces with the calibration database see more instruction here
https://wcte.hyperk.ca/documents/calibration-db-apis/v1-api-endpoints-documentation
Currently processed for the test database - to be updated when the production database 
is ready. The authentication requires a credential text file ./.wctecaldb.credential 
to be in the current working directory - more details in the database interface above

## PMTMapping 

PMTMapping is a class containing the mapping of the WCTE PMTs slot and position ids to the
electronics channel and mPMT card ids and vice versa
Usage:
mapping = PMTMapping()
mapping.get_slot_pmt_pos_from_card_pmt_chan(card_id,pmt_channel) returns the slot and pmt position
and 
mapping.get_card_pmt_chan_from_slot_pmt_pos(slot_id,pmt_position) returns the card and channel
The mapping json is located in the package

## DetectorGeometry

Class to load PMT positions, directions and calculate time of flight.


