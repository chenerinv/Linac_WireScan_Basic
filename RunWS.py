# our temporary GUI
import mainws
import logging
import time
import os

##### #TODO EDIT ME #####
maindir = "C:/Users/erinchen/Documents/VS/ConstantSpeedWS/" # a new directory with unix timestamp will be made in this directory
modstr = "D12"
setp = [12700,-12700] # the two possible setpoints issued
cutoff = [14,-40] # readback cutoffs for recording data 
addparam = [] # list of strings of additional parameters you'd like to add
stringnote = "stringnote: test to see if it works 1/17/2024"
#########################

# create folder & start logging
inittime = round(time.time())
savepath = maindir+str(inittime)+"_WS/"
if not os.path.exists(savepath):
    os.makedirs(savepath)
logging.basicConfig(filename=savepath+str(inittime)+"_log.log", level = logging.INFO) # format='%(levelname)s:%(message)s', 
logging.info(stringnote)

# start wire scan
logging.info('Started mainws')
mainws.mainws(modstr,setp,cutoff,addparam,savepath)
logging.info('Finished mainws')