# module for organizing acsys dictionary outputs
import logging
logger = logging.getLogger(__name__)

def data_proc(indict,addparam): 
    # indict = {
    #     'tags': [],
    #     'data': [],
    #     'stamps': []
    # }

    outdict = {
        'pxdata': [],
        'pydata': [],
        'pudata': [],
        'sxdata': [],
        'sydata': [],
        'sudata': [],
        'stamps': []
    }
    for item in addparam: # extending the outdict to include the added parameters
        outdict[item] = []

    errors = [] # keep a record of errors 

    for i in range(len(indict['tags'])): # looping over index for each entry in list
        if indict['tags'][i]  == 0: 
            pass
        elif indict['tags'][i]  == 1: 
            outdict['pxdata'] += [indict['data'][i]] # append the one number to the list
            outdict['stamps'] += [indict['stamps'][i]]
        else: 
            # check that the stamps for the other tags match the stamp of the previous tag
            try: # this is needed because the first data point is usually a quad value not a ws value
                if outdict['stamps'][-1] != indict['stamps'][i]: 
                    logger.info("Warning! A stamp that should match doesn't match...we took the first value. "+str(outdict['stamps'][-1])+" "+str(indict['stamps'][i]))
                    errors.append(1)
                    # a more urgent error is not necessary because the data should be viewed independent of time anyways
            except Exception as err: 
                logger.warning("An Exception occurred: "+str(err))
                errors.append(3)

            # based on tag value, append number to list
            if indict['tags'][i]  == 2: 
                outdict['pydata'] += [indict['data'][i]] 
            elif indict['tags'][i]  == 3: 
                outdict['pudata'] += [indict['data'][i]] 
            elif indict['tags'][i]  == 4: 
                outdict['sxdata'] += [indict['data'][i]] 
            elif indict['tags'][i]  == 5: 
                outdict['sydata'] += [indict['data'][i]] 
            elif indict['tags'][i]  == 6: 
                outdict['sudata'] += [indict['data'][i]] 
            elif indict['tags'][i] > 6:
                outdict[addparam[indict['tags'][i]-7]] += [indict['data'][i]]

    # final check that the stamps processed properly -- check list lengths
    for key in list(outdict.keys()): 
        if (len(outdict['stamps']) != len(outdict[key])): 
            errors.append(2)
            logger.info("Warning! Stamp list isn't same length as "+key+" list.")

    return outdict, errors

if __name__ == '__main__':
    data_proc()