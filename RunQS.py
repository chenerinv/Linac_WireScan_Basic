# our temporary GUI
import mainqs
import logging
import time
import os

##### #TODO EDIT ME #####
userinput = {
    "Out Limit": -40.0,
    "In Limit": 14.0,
    "Steps": 12700,
    "Event": "0C",
    "Additional Parameters": ["L:GR2MID"],
    "Save Directory": "C:/Users/erinchen/Documents/VS/Git_Projects/Linac_WireScan_Basic/datacollect",
    
    "Wires": ["D03","D02"],
    "Quad Name": "G:AMANDA",
    "Quad Vals": [60,65,70,75,80],
    "QS User Comment": "program test",
}
#########################

mainqs.mainqs(userinput)

