import acsyscontrol as ac
import mainws
import matplotlib.pyplot as plt
import wsanalysis
import csvdictparse as cdp
import logging
logger = logging.getLogger(__name__)

def mainqs(quadvals,quadname,modstr,setp,cutoff,savepath): 
    # check and save current quad value
    quads = ac.checkparam(str(quadname)+".SETTING",10)[0]
    logger.info(quadname+" initial setting value is "+str(quads))
    quadinit = ac.checkparam(str(quadname)+".READING",10)[0]
    logger.info(quadname+" initial reading value is "+str(quadinit))
    
    # initialize list of data for quadscan plot
    qdata = {
        'quadsets': quadvals, 
        'qreal': [], # just a list
        'qerr': [], # just a list
        'wsid': [], # just a list
        'wssigma': [], # a list of 3-element-lists
        'wssigmaerr': [], # a list of 3-element-lists
        'wsr2': [] # a list of 3-element-lists
    }

    # intialize plot
    colors = ["brown", "orange", "mediumseagreen"]
    markers = ["o","v","s"]
    legend = ["x","y","u"]
    plt.figure()
    plt.xlim((min(quadvals)-5),max(quadvals)+1) # quad reading tends to skew low
    plt.xlabel("Quadrupole Current Readback (A)")
    plt.ylabel("Gaussian RMS Width of Beam at WS Position (mm)")
    plt.show(block=False) 
    plt.draw()

    for current in quadvals: 
        # change quad value to setpoint and confirm 
        ac.setconfirm(quadname,current)

        # run wire scanner program
        utime, siglist, sigerr, r2s, dpresults = mainws.mainws(modstr,setp,cutoff,[quadname],savepath)
        
        # save data for quadscan plot
        qavg, qstd = wsanalysis.avg(dpresults[quadname])
        qdata['wsid'] += [utime]
        qdata['wssigma'] += [siglist]
        qdata['wssigmaerr'] += [sigerr]
        qdata['wsr2'] += [r2s]
        qdata['qreal'] += [qavg]
        qdata['qerr'] += [qstd]

        # update plot with data
        for i in range(3): 
            try:
                if qdata['wssigmaerr'][-1][i] > 5: 
                    plt.plot(qdata['qreal'][-1],qdata['wssigma'][-1][i],marker="x",color=colors[i], label=legend[i])
                else: 
                    plt.errorbar(qdata['qreal'][-1],qdata['wssigma'][-1][i],yerr = qdata['wssigmaerr'][-1][i], xerr = qdata['qerr'][-1], marker=markers[i],color=colors[i], label=legend[i]) # incorporate errors
            except Exception as err: 
                logger.warning("An Exception occurred for "+str(qdata['wsid'][-1])+": "+str(err))
        plt.draw()

    # reset quad value with setpoint
    ac.setconfirm(quadname,quads)

    # save quadscan data summary
    cdp.tocsv(qdata,savepath+"_".join([str(qdata['wsid'][0]),quadname.replace(":",""),modstr,"datasummary"]))

    # do the parabolic fit & save data
    parabdict, lines = wsanalysis.parab_fit(qdata['qreal'],qdata['wssigma']) # a list and a list of 3-part (xyu) lists
    for i in range(3):
        try:
            plt.plot(lines['xs'][i],lines['ys'][i],color = colors[i])
        except Exception as err: 
            logger.warning("An Exception occurred for "+str(qdata['wsid'][-1])+": "+str(err))
    plt.draw()
    cdp.tocsv(parabdict,savepath+"_".join([str(qdata['wsid'][0]),quadname.replace(":",""),modstr,"parabfit"]))

    # saving figure
    plt.savefig(savepath+"_".join([str(qdata['wsid'][0]),quadname.replace(":",""),modstr,"plot"])+".png") # using the first ws's time marker
    print("All done. Please close plot after examination to close out the code.")
    plt.show()

if __name__ == '__main__':
    mainqs()