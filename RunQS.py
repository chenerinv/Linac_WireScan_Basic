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
    "Event": "0A",
    "Additional Parameters": ["L:D5TOR","L:D7TOR","L:D53LM","L:D54LM","L:D61LM","L:D62LM","L:D63LM","L:D64LM","L:D71LM"],
    "Save Directory": "C:/Users/erinchen/Documents/VS/Git_Projects/Linac_WireScan_Basic/2024_07_Studies_Data/QS_3_Q54_D63",
    
    "Wires": ["D63"],
    "Quad Name": "L:Q54",
    "Quad Vals": [170,180],
    "QS User Comment": "QS3",
}
#########################

mainqs.mainqs(userinput)

