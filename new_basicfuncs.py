import json
import csv
import datetime
import numpy as np
import itertools
import new_basicdata as basicdata
import numpy as np

def checktype(value,type):
    """Check the type of a value: int, float, string, etc."""
    if type == int: 
        try: 
            f = float(value)
            if f.is_integer() is True: 
                i = int(value) 
                return True, i
            else: 
                return False, value
        except: 
            return False, value
    elif type == float: 
        try: 
            f = float(value)
            return True, f
        except: 
            return False, value 
    else: # strings and list
        return isinstance(value,type), value

def strtonum(value): 
    f = float(value)
    if f.is_integer() is True: 
        f = int(value) 
    return f

def dicttojson(indict,jsonstr): 
    """Save dict as a json."""
    outdict = indict.copy()
    for item in ["Additional Parameters", "Monitors", "Monitor Min", "Monitor Max"]: 
        if item in list(outdict.keys()): 
            outdict[item] = ", ".join([str(i) for i in outdict[item]])
    for key in indict: # added 8/2/2024 so we wouldn't end up with NaNs in JSONs
        if isinstance(indict[key],float):
            if math.isnan(indict[key]): indict[key] = None
    if jsonstr[-5:] != ".json": 
        jsonstr += ".json"
    with open(jsonstr,"w") as outfile: 
        json.dump(outdict,outfile)

def dicttocsv(indict,csvstr): 
    """Save dict as a csv."""
    if csvstr[-4:] != ".csv": 
        csvstr +=".csv"
    with open(csvstr,"w",newline='') as f: # NOTE: the newline thing is because of windows & Python3. probably take out for non windows?
        csvw = csv.writer(f)
        csvw.writerow(indict.keys())
        csvw.writerows(itertools.zip_longest(*indict.values())) # zip would crop to the shortest list in the dict, using itertools instead
    f.close()
    return 

def csvtodict(csvstr): 
    """Import a csv as a dict."""
    def convert(st): 
        try:
            if ((len(st) > 0) and (st[0] == "[")): # list 
                li = st.strip('][').split(', ') 
                for i in range(len(li)): 
                    li[i] = convert(li[i]) # recursively processing list
                return li
            else:
                f = float(st) # float
                if f%1 == 0:
                    return int(f) # int
                return f
        except ValueError:
            if st == "nan": # string
                return np.nan
            return st

    reader = csv.DictReader(open(csvstr))
    outdict = {}
    firstrow = 0
    for row in reader: 
        if firstrow == 0: # initialize lists
            for item in list(row.keys()): 
                outdict[item]=[]
            firstrow += 1
        for item in list(row.keys()): # add to list 
            num = convert(row[item]) 
            outdict[item] += [num]    
    return outdict

def rawtowires(indict,modstr): 
    """Convert raw format data from acsys into a dict with keys for each wire."""
    def checklengths(): 
        """Do a check that each wire has the same amount of data for that time, or fill in the gaps."""
        keylens = []
        for key in keylist: 
            keylens.append(len(outdict[key]))
        if max(keylens) - min(keylens) == 1: 
            # execute corrective action
            for j,length in enumerate(keylens): 
                if length < max(keylens): 
                    outdict[keylist[j]].append(np.nan)
        elif max(keylens) - min(keylens) > 1: 
            print("Something unexpected occurred. Please look at the data individually.")

    outdict = {}
    tagdict = {}
    j = 1
    keylist = basicdata.pdict[modstr]+basicdata.sdict[modstr]
    for key in keylist: # this assumes that we use the same pattern, which is fine
        outdict[key] = []
        tagdict[j] = key
        j=j+1
    
    currentstamp = 0
    for rownum in range(len(indict["tags"])): 
        # we check as to whether we've moved to a new time
        if indict['stamps'][rownum] != currentstamp: 
            currentstamp = indict['stamps'][rownum]
            # check that all the data are the same length, for the ones that aren't, append np.Nan
            checklengths()
        if indict["tags"][rownum] in tagdict.keys():
            outdict[tagdict[indict["tags"][rownum]]].append(indict["data"][rownum])
    checklengths() # need to call again to check that the last set rounded off right.
    return outdict

def avgtag(indict,tagkey): 
    """."""
    data = []

    for i, tag in enumerate(indict["tags"]): 
        if str(tag) == str(tagkey): 
            data.append(indict["data"][i]) 

    if len(data) >= 1: 
        avg = sum(data)/len(data)
        length = len(data)
        std = np.std(np.array(data))
        return avg, std, length
    else: 
        return False,False,False

def currtokl(current,beta,energyMeV): 
    me, mp, c, l = 0.511006, 938.27, 299.792458, 85.3
    mh = me+mp
    sub = -92.6639720014948 # scaling factor
    betagamma = 0.513266511360034

    sol = 2.99*10**8 #m/s
    #beta = 0.456630784
    Kval = 0.1338 # T/m/A
    energy = (energyMeV+mh)*10**6 # eV
    length = basicdata.quadlength # m

    # bprime = current*Kval #current+sub
    # bpl = bprime*l/1000
    # f = betagamma*(mh/c)/bpl
    #kl = 1/f # 1/m

    kl = Kval*current*sol*length/(beta*energy)

    return kl

if __name__ == "__main__":
    checktype()