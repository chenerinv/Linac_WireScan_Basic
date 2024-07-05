#import new_acsyscontrol as acsyscontrol
from new_acsyscontrol import acsyscontrol as acs
import new_basicdata as basicdata
import new_basicfuncs as basicfuncs
import time
import os

import mainws
import matplotlib.pyplot as plt
import wsanalysis
import csvdictparse as cdp
import logging
logger = logging.getLogger(__name__)

def mainws(userinput,acsyscontrol): 

    """Execute the setup needed for a scan and start the scan."""
    # locking to modification
    scan_thread = "mainscan"
    # check thread isn't open+unset or open+set+incomplete
    # if scan_thread in acsyscontrol.get_list_of_threads(): # if thread exists and is unset
    #     print("Starting another scan is not allowed. Another scan is ongoing.\n")
    #     return
    # elif acsyscontrol.check_finally(scan_thread) is False:  # or if thread exists, is set, but finally isn't done (to accomodate lack of joining in abort)
    #     print("Starting another scan is not allowed. Another scan is closing.\n")
    #     return 
    # checking there's no missing keys 
    for item in basicdata.requiredkeys: 
        if item not in list(userinput.keys()): 
            print(item+" is a required value.\n") 
            return 
        
    # check that the wire is in an ok position 
    temppos = float(acsyscontrol.checkparam([basicdata.pdict[userinput["Wire"]][0]],10)[0])
    if temppos <= userinput["Out Limit"]: 
        userinput["Direction"] = 0 # 0 for going in, 1 for going out
    elif temppos >= userinput["In Limit"]: 
        userinput["Direction"] = 1
    else: 
        print(basicdata.pdict[userinput["Wire"]][0]+" is not outside In/Out Limit.\n")
        return       
    
    # things that doesn't need to be saved in setup parameters (some still are) but needs to be accessible by scan
    userinput["Timestamp"] = round(time.time()) # choose unix time stamp around now 
    # make directory
    savepath = os.path.join(userinput["Save Directory"],str(userinput["Timestamp"])+"_"+userinput["Wire"]).replace("\\","/")
    if not os.path.exists(savepath): 
        os.makedirs(savepath)
        userinput["WS Directory"] = savepath
    else: 
        print("Folder for data unable to be created.\n")
        return
    basicfuncs.dicttojson(userinput,os.path.join(userinput["WS Directory"],"_".join([str(userinput["Timestamp"]),userinput["Wire"],"SetupParameters.json"])))
    # make dict of tags
    tagdict, i = {}, 1
    for device in basicdata.pdict[userinput['Wire']]+basicdata.sdict[userinput['Wire']]+userinput['Additional Parameters']:
        tagdict[i]=device
        i=i+1
    userinput["Tags"] = tagdict

    # collect metadata 
    metad = {key:userinput[key] for key in ['Event', 'User Comment','Timestamp','WS Directory','Direction','Tags']}
    if userinput["Event"] == "0A": 
        params = ["L:SOURCE.READING","L:D7TOR.READING","L:TCHTON.READING","L:TCHTOF.READING","L:BSTUDY.READING"]
    else: 
        params = ["L:SOURCE.READING","L:D7TOR.READING"]
    m = acsyscontrol.checkparam(params,10)
    if m[0] == -10.24:
        metad["Source"] = "A"
    elif m[0] == 10.24: 
        metad["Source"] = "B"
    metad["L:D7TOR"] = m[1]
    if len(params) == 5: 
        metad["Pulse Length"] = m[3]-m[2]
        metad["Frequency"] = m[4]
    basicfuncs.dicttojson(metad,os.path.join(userinput["WS Directory"],"_".join([str(userinput["Timestamp"]),userinput["Wire"],"Metadata.json"])))
    
    # start wirescan 
    print("Scan initiated.")
    acsyscontrol.start_scan_thread(scan_thread,userinput)
    return userinput["Timestamp"], userinput["WS Directory"]

if __name__ == '__main__':
    mainws()