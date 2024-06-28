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

def mainqs(userinput): 
    acsyscontrol = acs()

    """Execute the setup needed for a scan and start the scan."""
    # locking to modification
    scan_thread = "mainscan"
    # check thread isn't open+unset or open+set+incomplete
    if scan_thread in acsyscontrol.get_list_of_threads(): # if thread exists and is unset
        print("Starting another scan is not allowed. Another scan is ongoing.\n")
        return
    elif acsyscontrol.check_finally(scan_thread) is False:  # or if thread exists, is set, but finally isn't done (to accomodate lack of joining in abort)
        print("Starting another scan is not allowed. Another scan is closing.\n")
        return
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
    metad["Abort"] = False
    basicfuncs.dicttojson(metad,os.path.join(userinput["WS Directory"],"_".join([str(userinput["Timestamp"]),userinput["Wire"],"Metadata.json"])))
    
    # start wirescan 
    acsyscontrol.start_scan_thread(scan_thread,userinput)
    print("Scan initiated.\n")

    def abortbutton(): 
        """Abort an ongoing scan."""
        try: 
            if scan_thread in acsyscontrol.get_list_of_threads(): # kill existing thread if present
                acsyscontrol.end_any_thread(scan_thread)
                print("Scan aborted by user.\n") 
                wiresout() # think more about this
                # record that an abort occurred by editing the metadata file
                metad["Abort"] = True
                basicfuncs.dicttojson(metad,os.path.join(userinput["WS Directory"],"_".join([str(userinput["Timestamp"]),userinput["Wire"],"Metadata.json"])))
            else: 
                print("No scan to abort.\n")
        except AttributeError: 
            print("No scan to abort.\n") 

    def wiresout():
        """Issue setting to move wire to the out position."""
        if userinput["Wire"].strip() in basicdata.pdict.keys():
            try: 
                acsyscontrol.setparam(basicdata.pdict[userinput["Wire"].strip()][0],-12700)
                print("Out setting issued to "+basicdata.pdict[userinput["Wire"].strip()][0]+".\n")
            except ValueError:
                print("Invalid Kerberos realm.\n") 
        else: 
            print("No wire selected, cannot pull wire out.\n")


    #TODO have something monitor the status of the thread and watch for an input? don't use a prompt in the input, issue one message and then 
    # repeatedly loop to updated thread status and re-request an input? 
    # typedinput = ""
    
    # while typedinput not in ["abort","wo"]:
    typedinput = input("Type 'abort' to abort scan or 'wo' to pull the wires out. ")

    if typedinput == 'abort': 
        abortbutton()
        return
    elif typedinput == 'wo': 
        wiresout()

    
        

    # check and save current quad value
    # quads = ac.checkparam(str(quadname)+".SETTING",10)[0]
    # logger.info(quadname+" initial setting value is "+str(quads))
    # quadinit = ac.checkparam(str(quadname)+".READING",10)[0]
    # logger.info(quadname+" initial reading value is "+str(quadinit))
    
    # # initialize list of data for quadscan plot
    # qdata = {
    #     'quadsets': quadvals, 
    #     'qreal': [], # just a list
    #     'qerr': [], # just a list
    #     'wsid': [], # just a list
    #     'wssigma': [], # a list of 3-element-lists
    #     'wssigmaerr': [], # a list of 3-element-lists
    #     'wsr2': [] # a list of 3-element-lists
    # }

    # # intialize plot
    # colors = ["brown", "orange", "mediumseagreen"]
    # markers = ["o","v","s"]
    # legend = ["x","y","u"]
    # plt.figure()
    # plt.xlim((min(quadvals)-5),max(quadvals)+1) # quad reading tends to skew low
    # plt.xlabel("Quadrupole Current Readback (A)")
    # plt.ylabel("Gaussian RMS Width of Beam at WS Position (mm)")
    # plt.show(block=False) 
    # plt.draw()

    # for current in quadvals: 
    #     # change quad value to setpoint and confirm 
    #     ac.setconfirm(quadname,current)

    #     # run wire scanner program
    #     utime, siglist, sigerr, r2s, dpresults = mainws.mainws(modstr,setp,cutoff,[quadname],savepath)
        
    #     # save data for quadscan plot
    #     qavg, qstd = wsanalysis.avg(dpresults[quadname])
    #     qdata['wsid'] += [utime]
    #     qdata['wssigma'] += [siglist]
    #     qdata['wssigmaerr'] += [sigerr]
    #     qdata['wsr2'] += [r2s]
    #     qdata['qreal'] += [qavg]
    #     qdata['qerr'] += [qstd]

    #     # update plot with data
    #     for i in range(3): 
    #         try:
    #             if qdata['wssigmaerr'][-1][i] > 5: 
    #                 plt.plot(qdata['qreal'][-1],qdata['wssigma'][-1][i],marker="x",color=colors[i], label=legend[i])
    #             else: 
    #                 plt.errorbar(qdata['qreal'][-1],qdata['wssigma'][-1][i],yerr = qdata['wssigmaerr'][-1][i], xerr = qdata['qerr'][-1], marker=markers[i],color=colors[i], label=legend[i]) # incorporate errors
    #         except Exception as err: 
    #             logger.warning("An Exception occurred for "+str(qdata['wsid'][-1])+": "+str(err))
    #     plt.draw()

    # # reset quad value with setpoint
    # ac.setconfirm(quadname,quads)

    # # save quadscan data summary
    # cdp.tocsv(qdata,savepath+"_".join([str(qdata['wsid'][0]),quadname.replace(":",""),modstr,"datasummary"]))

    # # do the parabolic fit & save data
    # parabdict, lines = wsanalysis.parab_fit(qdata['qreal'],qdata['wssigma']) # a list and a list of 3-part (xyu) lists
    # for i in range(3):
    #     try:
    #         plt.plot(lines['xs'][i],lines['ys'][i],color = colors[i])
    #     except Exception as err: 
    #         logger.warning("An Exception occurred for "+str(qdata['wsid'][-1])+": "+str(err))
    # plt.draw()
    # cdp.tocsv(parabdict,savepath+"_".join([str(qdata['wsid'][0]),quadname.replace(":",""),modstr,"parabfit"]))

    # # saving figure
    # plt.savefig(savepath+"_".join([str(qdata['wsid'][0]),quadname.replace(":",""),modstr,"plot"])+".png") # using the first ws's time marker
    # print("All done. Please close plot after examination to close out the code.")
    # plt.show()

if __name__ == '__main__':
    mainqs()