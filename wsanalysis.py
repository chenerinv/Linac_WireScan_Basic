# module for analyzing wire scanner data (fitting, plotting, calculations)
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as sp
from scipy.optimize import curve_fit as cf
import logging
logger = logging.getLogger(__name__)

def onews_fit(indict,uniquetime,modstr,savepath): 
    def gauss(x,a,x_mean,std,c):
        return a*np.exp(-(x-x_mean)**2/(2*std**2))+c   

    # indict = {
    #     'pxdata': [],
    #     'pydata': [],
    #     'pudata': [],
    #     'sxdata': [],
    #     'sydata': [],
    #     'sudata': [],
    #     'stamps': []
    # }

    wirelist = ["x","y","u"]
    errorstat = []

    fitinfo = {
        'wire': wirelist,
        'peak': [], # each list is of x, y, u
        'peakerr': [],
        'sigma': [],
        'sigmaerr': [],
        'amp': [],
        'amperr': [],
        'float': [],
        'floaterr': [],
        'r2': []        
    }
    
    for i in range(len(wirelist)): 
        xs = indict["p"+wirelist[i]+"data"] # position
        ys = indict["s"+wirelist[i]+"data"] # signal

        mean = 0
        yval = ys[0]
        for k in range(1,len(xs)): # detection scheme to find lowest point
            if ys[k] < yval:
                mean = xs[k]
                yval = ys[k]
        try: 
            padd, cadd = cf(gauss, xs, ys, p0 = [-0.5, mean, 2.5, 0], bounds = [(-5,-75,-10,-0.4), (0,75,10,0.4)])
            errorstat.append(0)
        except Exception as err: 
            logger.warning("An Exception occurred: "+str(err))
            errorstat.append(1)
      
        if errorstat[-1] == 0: # if gaussian fit was successful
            res = ys-gauss(xs,*padd)
            ss_res = np.sum(res**2)
            ss_tot = np.sum((ys-np.mean(ys))**2)

            plt.figure()
            plt.scatter(xs,ys)
            plt.plot(xs,[gauss(x,padd[0],padd[1],padd[2],padd[3]) for x in xs],color='red')
            plt.xlabel("Position (mm)")
            plt.ylabel("Intensity (V)")
            plt.title(" ".join([modstr,wirelist[i]]))
            plt.show(block=False)
            plt.savefig(savepath+"_".join([str(uniquetime),modstr,wirelist[i],"plot"])+".png")
            plt.close()

            fitinfo['peak'] += [padd[1]]
            fitinfo['peakerr'] += [np.sqrt(cadd[1][1])]
            fitinfo['sigma'] += [padd[2]]
            fitinfo['sigmaerr'] += [np.sqrt(cadd[2][2])]
            fitinfo['amp'] += [padd[0]]
            fitinfo['amperr'] += [np.sqrt(cadd[0][0])]
            fitinfo['float'] += [padd[3]]
            fitinfo['floaterr'] += [np.sqrt(cadd[3][3])]
            fitinfo['r2'] += [1-(ss_res/ss_tot)]
        else: 
            fitinfo['peak'] += [None]
            fitinfo['peakerr'] += [None]
            fitinfo['sigma'] += [None]
            fitinfo['sigmaerr'] += [None]
            fitinfo['amp'] += [None]
            fitinfo['amperr'] += [None]
            fitinfo['float'] += [None]
            fitinfo['floaterr'] += [None]
            fitinfo['r2'] += [None]

    return fitinfo

def temp_linear(indict,uniquetime,modstr,savepath):
    def linear(x,m,b): # our test fit
        return m*x+b

    wirelist = ["x","y","u"]
    errorstat = []

    fitinfo = {
        'm': [],
        'b': [],
        'r': [],
        'p': [],
        'se': [],
        'wire': wirelist
    }

    for i in range(len(wirelist)): 
        xs = indict["p"+wirelist[i]+"data"] # position
        ys = indict["s"+wirelist[i]+"data"] # signal

        try: 
            slope, int, r, p, se = sp.linregress(xs, ys)
            errorstat.append(0)
        except Exception as err: 
            logger.warning("An Exception occurred: "+str(err))
            errorstat.append(1)
      
        if errorstat[-1] == 0: # if gaussian fit was successful
            plt.figure()
            plt.scatter(xs,ys)
            plt.plot(xs,[linear(x,slope,int) for x in xs],color='red')
            plt.xlabel("Position (mm)")
            plt.ylabel("Intensity (V)")
            plt.title(" ".join([modstr,wirelist[i]]))
            plt.show(block=False)
            plt.savefig(savepath+"_".join([str(uniquetime),modstr,wirelist[i],"plot"])+".png")

            fitinfo['m'] += [slope]
            fitinfo['b'] += [int]
            fitinfo['r'] += [r]
            fitinfo['p'] += [p]
            fitinfo['se'] += [se]
        else: 
            fitinfo['m'] += [None]
            fitinfo['b'] += [None]
            fitinfo['r'] += [None]
            fitinfo['p'] += [None]
            fitinfo['se'] += [None]

    return fitinfo

def avg(inlist): 
    avg = sum(inlist) / len(inlist)
    var = sum([((x - avg) ** 2) for x in inlist]) / len(inlist) 
    std = var ** 0.5
    return avg, std

def parab_fit(quadlist,sigmalistlist):  
    def parabola(x,a,b,c):
        return a*x**2 + b*x + c

    outdict = {
        'a': [], # 1-3 part list
        'b': [],
        'c': [],
        'aerr': [],
        'berr': [],
        'cerr': [],
        'r2': [],
    }
    errorstat = 0
    fitline = { # a separate dict because this isn't going to be saved to file
        'xs': [],
        'ys': []
    }

    for i in range(len(sigmalistlist[0])): # giving sigamlistlist flexibility to be 1 or more elements [[x1,y1,u1],[x1,y1,u1]], traditionally 3 (x y u)
        templist = []
        for j in range(len(sigmalistlist)): # generally corresponds to how many quad data points
            templist.append(sigmalistlist[j][i])
        try: 
            padd, cadd = cf(parabola, np.array(quadlist), np.array(templist))
        except Exception as err: 
            logger.warning("An Exception occurred: "+str(err))
            errorstat = 6 # a random nonzero value

        if errorstat == 0: # if parabolic fit was successful
            res = np.array(templist)-parabola(np.array(quadlist),*padd) 
            ss_res = np.sum(res**2)
            ss_tot = np.sum((templist-np.mean(templist))**2)
            outdict['a'] += [padd[0]]
            outdict['b'] += [padd[1]] 
            outdict['c'] += [padd[2]]
            outdict['aerr'] += [np.sqrt(cadd[0][0])]
            outdict['berr'] += [np.sqrt(cadd[1][1])] 
            outdict['cerr'] += [np.sqrt(cadd[2][2])]
            outdict['r2'] += [1-(ss_res/ss_tot)]           
            xs = np.linspace(min(quadlist)-5,max(quadlist)+1,100)
            ys = parabola(np.array(xs),*padd)
            fitline['xs'] += [xs]
            fitline['ys'] += [ys]
        else: 
            outdict['a'] += [None]
            outdict['b'] += [None] 
            outdict['c'] += [None]
            outdict['aerr'] += [None]
            outdict['berr'] += [None] 
            outdict['cerr'] += [None]
            outdict['r2'] += [None]
            fitline['xs'] += [None]
            fitline['ys'] += [None]

    return outdict, fitline

if __name__ == '__main__':
    onews_fit()
    temp_linear()
    avg()
    parab_fit()
