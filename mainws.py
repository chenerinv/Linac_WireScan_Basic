import acsyscontrol as ac
import dataprocess
import wsanalysis
import csvdictparse as cdp
import calendar
import logging
logger = logging.getLogger(__name__)

def mainws(modstr,setp,cutoff,addparam,savepath): 
    setind = 5 # arbitrary value that's not 0 or 1
    
    currpos, stamp = ac.checkparam("L:"+str(modstr)+"WPX.READING",10)  
    uniquetime = calendar.timegm(stamp.timetuple()) # stamp is a unixtime, gmt 
    logger.info("WS Identifier is "+str(uniquetime))

    if currpos > cutoff[0]: setind = 1 
    elif currpos < cutoff[1]: setind = 0 
    else: 
        logger.critical("Warning! Wire scanner is in the beampipe. Please move to a viable position.")
        return uniquetime # this will likely stop the program

    if setind < 2:
        results = ac.onews_proc(modstr,setp,cutoff,setind,addparam) # execute a wire scan
        cdp.tocsv(results,savepath+"_".join([str(uniquetime),modstr,"resultsraw"])) # save raw data
        dpresults, err = dataprocess.data_proc(results,addparam) # organize data
        logger.info("dpresults yields errors: "+str(err))
        cdp.tocsv(dpresults,savepath+"_".join([str(uniquetime),modstr,"resultsprocessed"])) # export organized data
        
        fitinfo = wsanalysis.onews_fit(dpresults,uniquetime,modstr,savepath) # execute gaussian fit & plotting
        cdp.tocsv(fitinfo,savepath+"_".join([str(uniquetime),modstr,"resultsfit"])) # save gaussian fit data

    return uniquetime, fitinfo['sigma'], fitinfo['sigmaerr'], fitinfo['r2'], dpresults

if __name__ == '__main__':
    mainws()