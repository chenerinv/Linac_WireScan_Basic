# module for using acsys -- data collection, setting, etc.
import acsys.dpm
import logging
logger = logging.getLogger(__name__)

def onews_proc(modstr,setp,cutoff,setind,addparam):     
    results = {
        'tags': [],
        'data': [],
        'stamps': []
    }

    async def onews(con):
        # setup context
        async with acsys.dpm.DPMContext(con,dpm_node="DPM03") as dpm:
            # configure setting:
            # check kerberos credentials and enable settings
            await dpm.enable_settings(role='linac_wirescan')
            # add acquisition requests
            await dpm.add_entry(0, 'L:'+modstr+'WPX.SETTING@N')                

            # configure entries for the parameters
            params = ['L:'+str(modstr)+'WPX','L:'+str(modstr)+'WPY','L:'+str(modstr)+'WPU',\
                      'L:'+str(modstr)+'WSX','L:'+str(modstr)+'WSY','L:'+str(modstr)+'WSU'] # default params for WS
            params += addparam # appending additional params
            tagcount = 1 # giving tags
            entries = [] # a list of tuples
            for i in range(len(params)): 
                entries.append((tagcount,params[i]+'@e,0a'))
                tagcount = tagcount + 1 

            await dpm.add_entries(entries) # add acquisition requests

            await dpm.apply_settings([(0, setp[setind])]) # set value 
            
            await dpm.start() # start acquisition

            # process incoming data. 
            async for evt_res in dpm:            
                if evt_res.isReading:
                    if evt_res.isReadingFor(0) is False:
                        # check for exit condition 
                        if evt_res.isReadingFor(1): 
                            posval = evt_res.data # getting the x position data specifically 
                        try: # this is mostly for if posval doesn't exist
                            if setind == 0: 
                                if posval > cutoff[setind]:
                                    logger.info("WS Done.")
                                    break # this is the exit condition
                            elif setind == 1:
                                if posval < cutoff[setind]: 
                                    logger.info("WS Done.")
                                    break # this is the exit condition
                        except Exception as err: 
                            logger.warning("An Exception occurred: "+str(err))
                    # save read data. must be last because we want the data to be the same length!
                    results['tags'] += [evt_res.tag]
                    results['data'] += [evt_res.data]
                    results['stamps'] += [evt_res.stamp] 
                else:
                    pass # this is likely a status response

    acsys.run_client(onews)
    return results

def checkparam(paramstr,tries): 
    result = {"val": [], "stamps":[]}
    async def checkp(con):
        # setup context
        async with acsys.dpm.DPMContext(con,dpm_node="DPM03") as dpm:
            # add acquisition requests
            await dpm.add_entry(0,paramstr) 

            # start acquisition
            await dpm.start()
            count1 = 0

            # process incoming data. Need better exit condition.
            async for it_res in dpm:
                if count1 < tries: 
                    if it_res.isReadingFor(0):
                        result["val"] += [it_res.data]
                        result["stamps"] += [it_res.stamp]
                        break
                    else:
                        count1 = count1+1
                        pass # this is likely a status response
                else:
                    break # it failed to get the data in the number of specified tries

    acsys.run_client(checkp)
    return result["val"][0], result["stamps"][0] 

def setconfirm(dev,current):
    async def setc(con):
        # setup context
        async with acsys.dpm.DPMContext(con,dpm_node="DPM03") as dpm:
            # check kerberos credentials and enable settings
            if dev[0] == "L":
                await dpm.enable_settings(role='linac_wirescan') 
            else: 
                await dpm.enable_settings(role='testing') 
            await dpm.add_entry(0, dev+'.SETTING@N')
            await dpm.apply_settings([(0, current)]) # steps to go from ~-50 to f20.

    acsys.run_client(setc)
    logger.info(dev+" set to "+str(current)+".")

if __name__ == '__main__':
    onews_proc()
    checkparam()
    setconfirm()


# TODO EXPAND TO DO ALARM ETC.  
# ,dpm_node="DPM03" is a workaround to make sure i don't infect all the dpms (0-8). call Charlie King if having issues. 