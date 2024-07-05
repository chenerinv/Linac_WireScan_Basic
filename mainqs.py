#import new_acsyscontrol as acsyscontrol
from new_acsyscontrol import acsyscontrol as acs
import new_basicdata as basicdata
import new_basicfuncs as basicfuncs
import time
import os
import json

import mainws
import matplotlib.pyplot as plt
import wsanalysis
import csvdictparse as cdp
import logging
import tkinter as tk
import copy
logger = logging.getLogger(__name__)

def appender(limit,listA): 
    while limit >= len(listA): 
        listA.append(False)

def mainqs(userinput): 
    acsyscontrol = acs()
    qdata = {
        'Quad Name': userinput["Quad Name"],
        'Quad Set Vals': userinput["Quad Vals"], 
        'User Comment': userinput["QS User Comment"],
        'Wires': {} # dict of dicts, {"D03":{},"D12":{}}
    }

    # make quad directory
    qdata["Timestamp"] = round(time.time()) # choose unix time stamp around now 
    # make directory
    savepath = os.path.join(userinput["Save Directory"],str(qdata["Timestamp"])+"_QS").replace("\\","/")
    if not os.path.exists(savepath): 
        os.makedirs(savepath)
        qdata["QS Directory"] = savepath
    else: 
        print("Folder for data unable to be created.\n")
        return

    # check and save current quad value
    qdata["Quad Init Set"] = acsyscontrol.checkparam([str(qdata["Quad Name"])+".SETTING"],10)[0]
    qdata["Quad Init Read"] = acsyscontrol.checkparam([str(qdata["Quad Name"])+".READING"],10)[0]
    if (qdata["Quad Init Set"] == False) or (qdata["Quad Init Read"] == False):
        print("Couldn't read quad values. Scan cancelled.")
        return 
    else: 
        print("Initial setting is: "+str(qdata["Quad Init Set"]))
        print("Initial reading is "+str(qdata["Quad Init Read"]))

    # make ws 
    for ws in userinput["Wires"]: 
        qdata["Wires"][ws] = { 
            'WS Timestamps': [], # just a list 
            'WS Paths': [], # just a list
            'WS Sigmas': [[],[],[]], # a list of 3-element-lists #TODO
            'WS Sigma Err': [[],[],[]], # a list of 3-element-lists #TODO
            'WS R2': [[],[],[]], # a list of 3-element-lists #TODO
            'Quad Real Vals': [], # just a list #TODO
            'Quad Real Weights': [],
            'Quad Err': [], # just a list #TODO
        }

    counterq = -1

    try: 
        for qval in qdata["Quad Set Vals"]: 
            counterq += 1
            for wire in list(qdata["Wires"].keys()):
                # do manipulation to configure wsinput 
                wsinput = copy.deepcopy(userinput)
                wsinput["Wire"] = wire
                wsinput["Additional Parameters"] = [qdata['Quad Name']]+wsinput["Additional Parameters"]
                # change user comment to include quad scan identifier
                wsinput["User Comment"] = "QS_ID_"+str(qdata["Timestamp"])
                acsyscontrol.setparam(qdata['Quad Name'],qval)
                timestamp, folderpath = mainws.mainws(wsinput,acsyscontrol)
                qdata["Wires"][wire]["WS Timestamps"] = timestamp
                qdata["Wires"][wire]["WS Paths"] = folderpath

                # # retrieve WS data and quad data
                def savestuff(tempdata,index): 
                    if tempdata["error"] == None: # checking there will actually be a sigma to reference
                        if counterq < len(qdata['Wires'][wire]['WS Sigmas'][index]): 
                            qdata['Wires'][wire]['WS Sigmas'][index][counterq] = tempdata["sigma"]
                        else: 
                            appender(counterq,qdata['Wires'][wire]['WS Sigmas'][index])
                            qdata['Wires'][wire]['WS Sigmas'][index][counterq] = tempdata["sigma"]
                        if counterq < len(qdata['Wires'][wire]['WS Sigma Err'][index]): 
                            qdata['Wires'][wire]['WS Sigma Err'][index][counterq] = tempdata["sigmaerr"]
                        else: 
                            appender(counterq,qdata['Wires'][wire]['WS Sigma Err'][index])
                            qdata['Wires'][wire]['WS Sigma Err'][index][counterq] = tempdata["sigmaerr"]
                        if counterq < len(qdata['Wires'][wire]['WS R2'][index]): 
                            qdata['Wires'][wire]['WS R2'][index][counterq] = tempdata["r2"]
                        else: 
                            appender(counterq,qdata['Wires'][wire]['WS R2'][index])
                            qdata['Wires'][wire]['WS R2'][index][counterq] = tempdata["r2"]
                    else: 
                        appender(counterq,qdata['Wires'][wire]['WS Sigmas'][index])
                        appender(counterq,qdata['Wires'][wire]['WS Sigma Err'][index])
                        appender(counterq,qdata['Wires'][wire]['WS R2'][index])

                # extracting wire scanner data, needs to be tested
                wsfiles = os.listdir(folderpath)
                searchkeys = ["X_GaussianFitStats.json","Y_GaussianFitStats.json","U_GaussianFitStats.json"]
                searchkeycheck = [0,0,0]
                for wsfile in wsfiles: 
                    if wsfile[-23:] in searchkeys: 
                        with open(os.path.join(folderpath,wsfile)) as jsonfile: 
                            tempdata = json.load(jsonfile)
                            savestuff(tempdata,searchkeys.index(wsfile[-23:]))
                            searchkeycheck[searchkeys.index(wsfile[-23:])] = 1
                    if wsfile[-13:] == "Metadata.json":
                        with open(os.path.join(folderpath,wsfile)) as jsonfile:
                            tempdata = json.load(jsonfile)
                            taglist = tempdata["Tags"]
                    if wsfile[-11:] == "RawData.csv":
                        rawdata = basicfuncs.csvtodict(os.path.join(folderpath,wsfile))

                for i,skey in enumerate(searchkeycheck):
                    if skey == 0: # accounting for if the file is missing
                        appender(counterq,qdata['Wires'][wire]['WS Sigmas'][i])
                        appender(counterq,qdata['Wires'][wire]['WS Sigma Err'][i])
                        appender(counterq,qdata['Wires'][wire]['WS R2'][i])

                qdatatag = 200
                # extracting quad scan data
                for tag in taglist: 
                    if taglist[tag] == qdata["Quad Name"]:
                        qdatatag = tag
                if qdatatag == 200: 
                    appender(counterq,qdata['Wires'][wire]['Quad Real Vals'])
                    appender(counterq,qdata['Wires'][wire]['Quad Real Weights'])
                    appender(counterq,qdata['Wires'][wire]['Quad Err'])
                else: 
                    avg, std, weight = basicfuncs.avgtag(rawdata,qdatatag)
                    if counterq < len(qdata['Wires'][wire]['Quad Real Vals']): 
                        qdata['Wires'][wire]['Quad Real Vals'][counterq] = avg
                        qdata['Wires'][wire]['Quad Real Weights'][counterq] = weight
                        qdata['Wires'][wire]['Quad Err'][counterq] = std

                    else: 
                        appender(counterq,qdata['Wires'][wire]['Quad Real Vals'])
                        qdata['Wires'][wire]['Quad Real Vals'][counterq] = avg
                        appender(counterq,qdata['Wires'][wire]['Quad Real Weights'])
                        qdata['Wires'][wire]['Quad Real Weights'][counterq] = weight
                        appender(counterq,qdata['Wires'][wire]['Quad Err'])
                        qdata['Wires'][wire]['Quad Err'][counterq] = std

    finally: 
        # save qs data
        basicfuncs.dicttojson(qdata,os.path.join(qdata["QS Directory"],"_".join([str(qdata["Timestamp"]),qdata["Quad Name"][2:],"Summary.json"])))
        # reset quad value with setpoint
        acsyscontrol.setparam(qdata["Quad Name"],qdata["Quad Init Set"])



    
    


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