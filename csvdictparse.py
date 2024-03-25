# module for converting between csv and dicts
import datetime
import calendar
import csv
import itertools
import logging
logger = logging.getLogger(__name__)

def tocsv(indict,csvstr):   
    # first converting to unix time
    keylist = list(indict.keys())
    for item in keylist: 
        if isinstance(indict[item][0],datetime.date):
            for i in range(len(indict[item])): 
                dt = indict[item][i] # already in gmt
                indict[item][i] = dt.timestamp() #calendar.timegm(dt.timetuple()) will round, while dt.timestamp() will keep milliseconds

    # writing dict to csv
    if csvstr[-4:] != ".csv": 
        csvstr +=".csv"
    with open(csvstr,"w",newline='') as f: # NOTE: the newline thing is because of windows & Python3. probably take out for non windows?
        csvw = csv.writer(f)
        csvw.writerow(indict.keys())
        csvw.writerows(itertools.zip_longest(*indict.values())) # zip would crop to the shortest list in the dict, using itertools instead
    f.close()
    logger.info("Data saved in "+csvstr)
    return 

def todict(csvstr): 
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
            if st == "None": # string
                return None
            return st

    # reading csv and writing to outdict
    if csvstr[-4:] != ".csv": 
        csvstr +=".csv"
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
            if item == 'stamps': # only support datetimes in stamps
                num = datetime.datetime.fromtimestamp(num)
            outdict[item] += [num]
    return outdict

if __name__ == '__main__':
    tocsv()
    todict()