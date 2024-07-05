import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit as cf
import new_basicdata as basicdata
import new_basicfuncs as basicfuncs
import os

class dataanalysis: 
    def __init__(self): 
        self.temp = []

    # basic functions
    def gauss(self,x,a,x_mean,std,c):
        return a*np.exp(-(x-x_mean)**2/(2*std**2))+c   
    def summedgauss(self,x,a1,mean,std1,c,a2,std2): # summed gaussian
        return a1*np.exp(-(x-mean)**2/(2*std1**2))+a2*np.exp(-(x-mean)**2/(2*std2**2))+c

    # fit methods
    def gaussfit(self,xparam,yparam,xlist,ylist):
        """Execute a Gaussian fit from provided data and return statistics."""
        # will save analysis data as a json later
        output = {
            'wirepos': xparam,
            'wiresig': yparam,
            'error': None
        }
        xlist = np.array(xlist)
        ylist = np.array(ylist)

        valid = ~(np.isnan(xlist)|np.isnan(ylist))
        mean = 0
        yval = ylist[0]
        for k in range(1,len(xlist)): # detection scheme to find lowest point
            if ylist[k] < yval:
                mean = xlist[k]
                yval = ylist[k]
        try: 
            padd, cadd = cf(self.gauss, xlist[valid], ylist[valid], p0 = [min(ylist), mean, 2.5, 0], bounds = [(min(ylist)-5,min(xlist)-5,-15,-0.5), (max(ylist)+5,max(xlist)+5,15,0.5)])
        except Exception as err: 
            output['error'] = str(err)
        
        if output['error'] == None: 
            res = ylist[valid]-self.gauss(xlist[valid],*padd)
            ss_res = np.sum(res**2)
            ss_tot = np.sum((ylist[valid]-np.mean(ylist[valid]))**2)

            output['amp'] = padd[0]
            output['amperr'] = np.sqrt(cadd[0][0])
            output['peak'] = padd[1]
            output['peakerr'] = np.sqrt(cadd[1][1])
            output['sigma'] = padd[2]
            output['sigmaerr'] = np.sqrt(cadd[2][2])
            output['float'] = padd[3]
            output['floaterr'] = np.sqrt(cadd[3][3])
            output['r2'] = 1-(ss_res/ss_tot)
        
        return output
    
    # summary of fit methods
    def endscanproc(self,procdata,coutput): 
        for i in range(len(basicdata.pdict[coutput["Wire"]])): 
            x = basicdata.pdict[coutput["Wire"]][i]
            y = basicdata.sdict[coutput["Wire"]][i]
            fitstats = self.gaussfit(x,y,procdata[x],procdata[y])
            basicfuncs.dicttojson(fitstats,os.path.join(coutput["WS Directory"],"_".join([str(coutput["Timestamp"]),coutput["Wire"],x[-1].upper(),"GaussianFitStats.json"])))
            # make standard plots based on data, save as png.
            if fitstats["error"] == None: 
                try: 
                    matplotlib.use('agg')
                    plt.figure()
                    plt.scatter(procdata[x],procdata[y],label="Raw Data")
                    xtemp = np.linspace(min(procdata[x]),max(procdata[x]),1000)
                    plt.plot(xtemp,[self.gauss(x,fitstats['amp'],fitstats['peak'],fitstats['sigma'],fitstats['float']) for x in xtemp],color='red',label="Gaussian Fit")
                    plt.xlabel("Position (mm)")
                    plt.ylabel("Intensity (V)")
                    plt.title(", ".join([coutput["Wire"],x[-1].upper()]))
                    plt.legend()
                    plt.savefig(os.path.join(coutput["WS Directory"],"_".join([str(coutput["Timestamp"]),coutput["Wire"],x[-1].upper(),"Plot.png"])))
                    plt.close()
                except: 
                    print("Plotting failed!")
            else: 
                try: 
                    matplotlib.use('agg')
                    plt.figure()
                    plt.scatter(procdata[x],procdata[y],label="Raw Data")
                    plt.xlabel("Position (mm)")
                    plt.ylabel("Intensity (V)")
                    plt.title(", ".join([coutput["Wire"],x[-1].upper()]))
                    plt.legend()
                    plt.savefig(os.path.join(coutput["WS Directory"],"_".join([str(coutput["Timestamp"]),coutput["Wire"],x[-1].upper(),"PlotRaw.png"])))
                    plt.close()
                except: 
                    print("Plotting failed!")

    # return list of data corresponding to the input parameters and dataset
    def generatefitline(self,inputnp,params,fit): 
        if fit == "gauss": 
            return [self.gauss(x,params['amp'],params['peak'],params['sigma'],params['float']) for x in inputnp]
        

    def parab_fit(quadlist,siglist):  
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
            'error': None,
        }
        fitline = { # a separate dict because this isn't going to be saved to file
            'xs': [],
            'ys': []
        }

        try: 
            padd, cadd = cf(parabola, np.array(quadlist), np.array(siglist))
        except Exception as err: 
            outdict["error"] = Exception # a random nonzero value

        if outdict["error"] == None: # if parabolic fit was successful
            res = np.array(siglist)-parabola(np.array(quadlist),*padd) 
            ss_res = np.sum(res**2)
            ss_tot = np.sum((siglist-np.mean(siglist))**2)
            outdict['a'] = padd[0]
            outdict['b'] = padd[1]
            outdict['c'] = padd[2]
            outdict['aerr'] = np.sqrt(cadd[0][0])
            outdict['berr'] = np.sqrt(cadd[1][1])
            outdict['cerr'] = np.sqrt(cadd[2][2])
            outdict['r2'] = 1-(ss_res/ss_tot)
            xs = np.linspace(min(quadlist)-5,max(quadlist)+5,100)
            ys = parabola(np.array(xs),*padd)
            fitline['xs'] = xs
            fitline['ys'] = ys
        else: 
            outdict['a'] = None
            outdict['b'] = None
            outdict['c'] = None
            outdict['aerr'] = None
            outdict['berr'] = None
            outdict['cerr'] = None
            outdict['r2'] = None
            fitline['xs'] = None
            fitline['ys'] = None

        return outdict, fitline