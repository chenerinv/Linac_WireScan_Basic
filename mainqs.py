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
import errorprop as ep
import numpy as np

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
                print("line78")
                timestamp, folderpath = mainws.mainws(wsinput,acsyscontrol)
                qdata["Wires"][wire]["WS Timestamps"].append(timestamp) # modified 10/14/2024 to actually append, not just save the last
                qdata["Wires"][wire]["WS Paths"].append(folderpath) # modified 10/14/2024 to actually append, not just save the last

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

    # plotting things
    colors = ["brown", "orange", "mediumseagreen"]

    for wire in qdata['Wires']: 
        # intialize plot
        plt.figure()
        #plt.xlim((min(quadvals)-5),max(quadvals)+1) # quad reading tends to skew low
        plt.xlabel("Quadrupole "+qdata["Quad Name"]+" Current Readback (A)")
        plt.ylabel("Gaussian RMS Width of Beam at WS "+wire+" Position (mm)")

        wires = ["X","Y","U"]
        for i,dir in enumerate(wires): 
            q = qdata["Wires"][wire]['Quad Real Vals']
            qerr = qdata["Wires"][wire]['Quad Err']
            sig = qdata["Wires"][wire]["WS Sigmas"][i] # mm
            serr = qdata["Wires"][wire]['WS Sigma Err'][i] # mm

            q = [x for i,x in enumerate(q) if sig[i] is not False]
            qerr = [x for i,x in enumerate(qerr) if sig[i] is not False]
            serr = [x for i,x in enumerate(serr) if sig[i] is not False] # mm
            sig = [x for i,x in enumerate(sig) if sig[i] is not False] # mm
            sig = [float('NaN') if sig[i] == None else x for i,x in enumerate(sig) ] # mm
            serr = [float('NaN') if serr[i] == None else x for i,x in enumerate(serr) ] # mm
            sig2 = [] # in mm2
            serr2 = [] # in mm2
            for num,val in enumerate(sig): # in mm2
                err = serr[num]
                g = ep.powC(2,(val,err))
                sig2.append(g[0])
                serr2.append(g[1])

            kl = [basicfuncs.currtokl(x, basicdata.beta[qdata["Quad Name"]],basicdata.energy[qdata["Quad Name"]]) for x in q]

            var = [] # in m^2
            verr = []
            for num,val in enumerate(sig): 
                err = serr[num]
                g = ep.multC(1/1000**2,ep.powC(2,(val,err))) # (value mm, error mm) 
                var.append(g[0])
                verr.append(g[1])

            plt.errorbar(q,sig,xerr=qerr,yerr=serr,ls='none',marker='o',color=colors[i],label=dir)

            qstats, fitline = dataana.parab_fit(q,sig2,serr2)
            if qstats["error"] == None: # if fit was successful, plot it
                plt.plot(fitline["xs"],fitline["ys"],color=colors[i],label=dir+" Fit")
                ynew = [np.sqrt(x) for x in fitline["ys"]]
                plt.plot(fitline["xs"],ynew,color=colors[i],label=dir+" Fit")

            # doing parabolic fit for kl
            realqstats = dataana.parab_fit(kl,var,verr)[0] 
            fitstatdict = {"raw": qstats, "kl": realqstats}

            # propogating uncertainty & calculating values
            padd = fitstatdict["kl"]["padd"]
            a, b, c = padd[0],padd[1],padd[2]
            cadd = fitstatdict["kl"]["cadd"]

            d = (basicdata.distances(wire[2:5])-basicdata.distances(qdata["Quad Name"]))/1000 # distance in m
            # adjusting cadd to account for d
            g = ep.powC(2,(d,0.005)) # assuming 5 mm std error, fixed 10/14/2024
            derr = g[1] 
            cadd = np.pad(cadd,((0,1),(0,1)),mode='constant',constant_values=0)
            cadd[3,3] = derr

            # calculating betagamma
            betagamma = basicdata.beta[qdata["Quad Name"]]*(1/np.sqrt(1-basicdata.beta[qdata["Quad Name"]]**2))

            # differentiation done in matlab for my sanity
            u_sig11 = a/d**2
            g_sig11 = [1/d**2, 0, 0, -(2*a)/d**3]
            e_sig11 = np.matmul(np.transpose(g_sig11),np.matmul(cadd,g_sig11))

            u_sig12 = -(2*a + b*d)/(2*d**3)
            g_sig12 = [-1/d**3, -1/(2*d**2), 0, (3*(2*a + b*d))/(2*d**4) - b/(2*d**3)]
            e_sig12 = np.matmul(np.transpose(g_sig12),np.matmul(cadd,g_sig12))

            u_sig22 = (c*d**2 + b*d + a)/d**4
            g_sig22 = [1/d**4, 1/d**3, 1/d**2, (b + 2*c*d)/d**4 - (4*(c*d**2 + b*d + a))/d**5]
            e_sig22 = np.matmul(np.transpose(g_sig22),np.matmul(cadd,g_sig22))

            u_emit = ((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)
            g_emit = [(a/d**6 - (8*a + 4*b*d)/(4*d**6) + (c*d**2 + b*d + a)/d**6)/(2*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)), -((2*a + b*d)/(2*d**5) - a/d**5)/(2*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)), a/(2*d**4*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)), ((3*(2*a + b*d)**2)/(2*d**7) + (a*(b + 2*c*d))/d**6 - (b*(2*a + b*d))/(2*d**6) - (6*a*(c*d**2 + b*d + a))/d**7)/(2*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2))]
            e_emit = np.matmul(np.transpose(g_emit),np.matmul(cadd,g_emit))

            u_alpha = (2*a + b*d)/(2*d**3*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2))
            g_alpha = [1/(d**3*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)) - ((2*a + b*d)*(a/d**6 - (8*a + 4*b*d)/(4*d**6) + (c*d**2 + b*d + a)/d**6))/(4*d**3*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2)), 1/(2*d**2*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)) + ((2*a + b*d)*((2*a + b*d)/(2*d**5) - a/d**5))/(4*d**3*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2)), -(a*(2*a + b*d))/(4*d**7*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2)), b/(2*d**3*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)) - (3*(2*a + b*d))/(2*d**4*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)) - ((2*a + b*d)*((3*(2*a + b*d)**2)/(2*d**7) + (a*(b + 2*c*d))/d**6 - (b*(2*a + b*d))/(2*d**6) - (6*a*(c*d**2 + b*d + a))/d**7))/(4*d**3*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2))]
            e_alpha = np.matmul(np.transpose(g_alpha),np.matmul(cadd,g_alpha))

            u_beta = a/(d**2*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2))
            g_beta = [1/(d**2*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)) - (a*(a/d**6 - (8*a + 4*b*d)/(4*d**6) + (c*d**2 + b*d + a)/d**6))/(2*d**2*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2)), (a*((2*a + b*d)/(2*d**5) - a/d**5))/(2*d**2*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2)), -a**2/(2*d**6*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2)), - (2*a)/(d**3*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)) - (a*((3*(2*a + b*d)**2)/(2*d**7) + (a*(b + 2*c*d))/d**6 - (b*(2*a + b*d))/(2*d**6) - (6*a*(c*d**2 + b*d + a))/d**7))/(2*d**2*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2))]
            e_beta = np.matmul(np.transpose(g_beta),np.matmul(cadd,g_beta))

            u_gamma = (c*d**2 + b*d + a)/(d**4*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2))
            g_gamma = [1/(d**4*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)) - ((c*d**2 + b*d + a)*(a/d**6 - (8*a + 4*b*d)/(4*d**6) + (c*d**2 + b*d + a)/d**6))/(2*d**4*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2)), 1/(d**3*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)) + (((2*a + b*d)/(2*d**5) - a/d**5)*(c*d**2 + b*d + a))/(2*d**4*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2)), 1/(d**2*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)) - (a*(c*d**2 + b*d + a))/(2*d**8*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2)), (b + 2*c*d)/(d**4*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)) - (4*(c*d**2 + b*d + a))/(d**5*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)) - ((c*d**2 + b*d + a)*((3*(2*a + b*d)**2)/(2*d**7) + (a*(b + 2*c*d))/d**6 - (b*(2*a + b*d))/(2*d**6) - (6*a*(c*d**2 + b*d + a))/d**7))/(2*d**4*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(3/2))]
            e_gamma = np.matmul(np.transpose(g_gamma),np.matmul(cadd,g_gamma))
            
            u_norme = 1000000*betagamma*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)
            g_norme = [(500000*betagamma*(a/d**6 - (8*a + 4*b*d)/(4*d**6) + (c*d**2 + b*d + a)/d**6))/((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2), -(500000*betagamma*((2*a + b*d)/(2*d**5) - a/d**5))/((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2), (500000*a*betagamma)/(d**4*((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)), (500000*betagamma*((3*(2*a + b*d)**2)/(2*d**7) + (a*(b + 2*c*d))/d**6 - (b*(2*a + b*d))/(2*d**6) - (6*a*(c*d**2 + b*d + a))/d**7))/((a*(c*d**2 + b*d + a))/d**6 - (2*a + b*d)**2/(4*d**6))**(1/2)]
            e_norme = np.matmul(np.transpose(g_norme),np.matmul(cadd,g_norme))

            fitstatdict["kl"]["padd"] = fitstatdict["kl"]["padd"].tolist()
            fitstatdict["kl"]["cadd"] = fitstatdict["kl"]["cadd"].tolist()
            fitstatdict["raw"]["padd"] = fitstatdict["raw"]["padd"].tolist()
            fitstatdict["raw"]["cadd"] = fitstatdict["raw"]["cadd"].tolist()
            fitstatdict["kl"]["sigma11"]=(u_sig11,np.sqrt(e_sig11))
            fitstatdict["kl"]["sigma12"]=(u_sig12,np.sqrt(e_sig12))
            fitstatdict["kl"]["sigma22"]=(u_sig22,np.sqrt(e_sig22))
            fitstatdict["kl"]["emittance"]=(u_emit,np.sqrt(e_emit))
            fitstatdict["kl"]["normemittance"]=(u_emit*betagamma*1000*1000,np.sqrt(e_emit*betagamma*1000*1000))
            fitstatdict["kl"]["alpha"]=(u_alpha,np.sqrt(e_alpha))
            fitstatdict["kl"]["beta"]=(u_beta,np.sqrt(e_beta))
            fitstatdict["kl"]["gamma"]=(u_gamma,np.sqrt(e_gamma))

            basicfuncs.dicttojson(fitstatdict,os.path.join(qdata["QS Directory"],"_".join([str(qdata["Timestamp"]),qdata["Quad Name"][2:],wire,dir,"ParabolicFitStats.json"])))

        plt.legend()
        plt.savefig(os.path.join(qdata["QS Directory"],"_".join([str(qdata["Timestamp"]),qdata["Quad Name"][2:],wire,"Plot"]))) # using the first ws's time marker

if __name__ == '__main__':
    mainqs()