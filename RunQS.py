# our temporary GUI
import mainqs
import logging
import time
import os

##### #TODO EDIT ME #####
userinput = {
    "Out Limit": -45.0,
    "In Limit": 14.0,
    "Steps": 12700,
    "Event": "0A",
    "Additional Parameters": ["L:D00LM","L:D0VLM","L:D11LM","L:D12LM","L:D13LM","L:D14LM","L:TO5OUT","L:D1TOR","L:D2TOR",],
    "Save Directory": "C:/Users/erinchen/Documents/VS/Git_Projects/Linac_WireScan_Basic//2024_10_Studies_Data/Tomography",
    
    "Wires": ["D12"],
    "Quad Settings File": "C:/Users/erinchen/Documents/VS/Git_Projects/Linac_WireScan_Basic/2024_10_Studies_Data/Tomography/tomog_quad_settings.csv",
    "QS User Comment": "testing tomog trial 1",
}
#########################

mainqs.mainqs(userinput)

