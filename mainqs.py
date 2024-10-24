#import new_acsyscontrol as acsyscontrol
from new_acsyscontrol import acsyscontrol as acs
import new_basicdata as basicdata
import new_basicfuncs as basicfuncs
from new_dataanalysis import dataanalysis as dataana
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
from errorprop import errorpropogation 
import numpy as np

def falseappender(limit,listA): 
    while limit >= len(listA): 
        listA.append(False)

def mainqs(userinput): 
    acsyscontrol = acs()
    ep = errorpropogation()
    qdata = {
        'Quad Settings File': userinput["Quad Settings File"],
        #'Quad Name': userinput["Quad Name"],
        #'Quad Set Vals': userinput["Quad Vals"], 
        'User Comment': userinput["QS User Comment"],
        'Wires': {} # dict of dicts, {"D03":{},"D12":{}}
    }

    # make quad directory
    qdata["Timestamp"] = round(time.time()) # choose unix time stamp around now 
    # make directory
    savepath = os.path.join(userinput["Save Directory"],str(qdata["Timestamp"])+"_TM").replace("\\","/")
    if not os.path.exists(savepath): 
        os.makedirs(savepath)
        qdata["QS Directory"] = savepath
    else: 
        print("Folder for data unable to be created.\n")
        return

    # open settings file, parse which quads, parse a list of lists [[1,2,3,4],[1,2,3,4]] for the set values & a list [a,b,c,d] of names
    inputfile = basicfuncs.csvtodict(qdata["Quad Settings File"])
    qdata["Quad Name"] = list(inputfile.keys()) # ["L:Q01", "L:Q02", "L:Q03", "L:Q04"]
    qdata["Quad Vals"] = []
    for i, quadname in enumerate(qdata["Quad Name"]): 
        for j in range(len(inputfile[quadname])): 
            if i == 0: 
                qdata["Quad Vals"].append([inputfile[quadname][j]])
            else: 
                qdata["Quad Vals"][j].append(inputfile[quadname][j])

    # check and save current quad value
    qdata["Quad Init Set"] = []
    qdata["Quad Init Read"] = []
    for i, quadname in enumerate(qdata["Quad Name"]): 
        qdata["Quad Init Set"].append(acsyscontrol.checkparam([str(quadname)+".SETTING"],10)[0])
        qdata["Quad Init Read"].append(acsyscontrol.checkparam([str(quadname)+".READING"],10)[0])
        if (qdata["Quad Init Set"][i] == False) or (qdata["Quad Init Read"][i] == False):
            print("Couldn't read quad values. Scan cancelled.")
            return 
        else: 
            print("Initial "+quadname+"setting is: "+str(qdata["Quad Init Set"][i]))
            print("Initial "+quadname+"reading is "+str(qdata["Quad Init Read"][i]))

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
        for n,qvals in enumerate(qdata["Quad Vals"]): 
            counterq += 1
            for wire in list(qdata["Wires"].keys()):
                # do manipulation to configure wsinput 
                wsinput = copy.deepcopy(userinput)
                wsinput["Wire"] = wire
                wsinput["Additional Parameters"] = qdata['Quad Name']+wsinput["Additional Parameters"]
                # change user comment to include quad scan identifier
                wsinput["User Comment"] = "TM_ID_"+str(qdata["Timestamp"])

                # set all 4 quads: 
                for i,qval in enumerate(qvals): 
                    acsyscontrol.setparam(qdata['Quad Name'][i],qval)
                
                timestamp, folderpath = mainws.mainws(wsinput,acsyscontrol)
                qdata["Wires"][wire]["WS Timestamps"].append(timestamp) # modified 10/14/2024 to actually append, not just save the last
                qdata["Wires"][wire]["WS Paths"].append(folderpath) # modified 10/14/2024 to actually append, not just save the last

#### CAN REMOVE THIS IF NECESSARY, it's just data extraction
                # retrieve WS data and quad data
                def savestuff(tempdata,index): 
                    if tempdata["error"] == None: # checking there will actually be a sigma to reference
                        if counterq < len(qdata['Wires'][wire]['WS Sigmas'][index]): 
                            qdata['Wires'][wire]['WS Sigmas'][index][counterq] = tempdata["sigma"]
                        else: 
                            falseappender(counterq,qdata['Wires'][wire]['WS Sigmas'][index])
                            qdata['Wires'][wire]['WS Sigmas'][index][counterq] = tempdata["sigma"]
                        if counterq < len(qdata['Wires'][wire]['WS Sigma Err'][index]): 
                            qdata['Wires'][wire]['WS Sigma Err'][index][counterq] = tempdata["sigmaerr"] # start the list
                        else: 
                            falseappender(counterq,qdata['Wires'][wire]['WS Sigma Err'][index])
                            qdata['Wires'][wire]['WS Sigma Err'][index][counterq] = tempdata["sigmaerr"]
                        if counterq < len(qdata['Wires'][wire]['WS R2'][index]): 
                            qdata['Wires'][wire]['WS R2'][index][counterq] = tempdata["r2"]
                        else: 
                            falseappender(counterq,qdata['Wires'][wire]['WS R2'][index])
                            qdata['Wires'][wire]['WS R2'][index][counterq] = tempdata["r2"]
                    else: 
                        falseappender(counterq,qdata['Wires'][wire]['WS Sigmas'][index])
                        falseappender(counterq,qdata['Wires'][wire]['WS Sigma Err'][index])
                        falseappender(counterq,qdata['Wires'][wire]['WS R2'][index])

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
                        falseappender(counterq,qdata['Wires'][wire]['WS Sigmas'][i])
                        falseappender(counterq,qdata['Wires'][wire]['WS Sigma Err'][i])
                        falseappender(counterq,qdata['Wires'][wire]['WS R2'][i])

                for i, quadname in enumerate(qdata["Quad Name"]):
                    if i == 0: 
                        qdata['Wires'][wire]['Quad Real Vals'].append([]) # instead of empty list, now we have an [[1,2,3,4],[]]
                        qdata['Wires'][wire]['Quad Real Weights'].append([]) # instead of empty list, now we have an [[1,2,3,4],[]]
                        qdata['Wires'][wire]['Quad Err'].append([]) # instead of empty list, now we have an [[1,2,3,4],[]]
                    qdatatag = 200
                    # extracting quad scan data
                    for tag in taglist: 
                        if taglist[tag] == quadname:
                            qdatatag = tag
                    if qdatatag == 200: # if we didn't actually find a tag, we'll need to add a False 
                        # falseappender doesn't work here because of the nested list structure; won't bother to check the list lengths, hopefully it's right? 
                        qdata['Wires'][wire]['Quad Real Vals'][counterq].append(False)
                        qdata['Wires'][wire]['Quad Real Weights'][counterq].append(False)
                        qdata['Wires'][wire]['Quad Err'][counterq].append(False)
                    else: # we found the tag! yippee! 
                        avg, std, weight = basicfuncs.avgtag(rawdata,qdatatag)
                        qdata['Wires'][wire]['Quad Real Vals'][counterq].append(avg)
                        qdata['Wires'][wire]['Quad Real Weights'][counterq].append(weight)
                        qdata['Wires'][wire]['Quad Err'][counterq].append(std)


    finally: 
        # save qs data
        basicfuncs.dicttojson(qdata,os.path.join(qdata["QS Directory"],"_".join([str(qdata["Timestamp"]),"Tomography","Summary.json"])))
        # reset quad values with setpoint
        for i,_ in enumerate(qdata['Quad Name']): 
            acsyscontrol.setparam(qdata['Quad Name'][i],qdata["Quad Init Set"][i])


if __name__ == '__main__':
    mainqs()