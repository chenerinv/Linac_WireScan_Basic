# our temporary GUI
import mainqs
import logging
import time
import os

##### #TODO EDIT ME #####
# maindir = "C:/Users/erinchen/Documents/VS/ConstantSpeedWS/" # a new directory with unix timestamp will be made in this directory
# quadvals = [135.4,134.4,133.4,132.4,135,132] # Add quad setpoints in the order you want executed
# quadname = "L:Q21"
# # main ws parameters
# modstr = "D12"
# setp = [12700, -12700] # the two possible setpoints issued 
# cutoff = [14,-40] # readback cutoffs for recording data 
# stringnote = "stringnote: "

userinput = {
    "Wire": "D03",
    "Out Limit": -40.0,
    "In Limit": 14.0,
    "Steps": 12700,
    "Event": "0C",
    "Additional Parameters": [],
    "Save Directory": "C:/Users/erinchen/Documents/VS/Git_Projects/Linac_WireScan_Basic/datacollect",
    "User Comment": "program test",

    "Quad Name": "G:AMANDA",
    "Quad Vals": [60,70,80],
}
#########################

# create folder & start logging
# inittime = round(time.time())
# savepath = maindir+str(inittime)+"_QS/"
# if not os.path.exists(savepath):
#     os.makedirs(savepath)
# logging.basicConfig(filename=savepath+str(inittime)+"_log.log", level = logging.INFO) 
# logging.info(stringnote)

# # start quad scan
# logging.info('Started mainqs')
mainqs.mainqs(userinput)
# logging.info('Finished mainqs')
