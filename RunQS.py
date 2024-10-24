# our temporary GUI
import mainqs
import logging
import time
import os

##### #TODO EDIT ME #####
userinput = {
    "Out Limit": -5.0,
    "In Limit": 12.0,
    "Steps": 12700,
    "Event": "0C",
    "Additional Parameters": ["L:D0VLM"],
    "Save Directory": "C:/Users/erinchen/Documents/VS/Git_Projects/Linac_WireScan_Basic/testing/20241014",
    
    "Wires": ["D12","D23"],
    "Quad Name": "L:Q04",
    "Quad Vals": [115,118,120,122],
    "QS User Comment": "testing trial 2",
}
#########################

mainqs.mainqs(userinput)

