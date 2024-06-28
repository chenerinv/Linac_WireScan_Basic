import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import os
import json
import time
import numpy as np

import basicdata
import basicfuncs
from acsyscontrol import acsyscontrol 
from dataanalysis import dataanalysis

class WireScanApp(tk.Toplevel):

    def startbutton(self,frame14): 
        """Execute the setup needed for a scan and start the scan."""
        # locking to modification
        self.scan_thread = "mainscan"
        # check thread isn't open+unset or open+set+incomplete
        if self.scan_thread in self.acsyscontrol.get_list_of_threads(): # if thread exists and is unset
            self.messageprint("Starting another scan is not allowed. Another scan is ongoing.\n")
            self.lockentries("enabled",basicdata.lockedentries,basicdata.lockedbuttons)
            return
        elif self.acsyscontrol.check_finally(self.scan_thread) is False:  # or if thread exists, is set, but finally isn't done (to accomodate lack of joining in abort)
            self.messageprint("Starting another scan is not allowed. Another scan is closing.\n")
            self.lockentries("enabled",basicdata.lockedentries,basicdata.lockedbuttons)
            return
        # main check to see if the setup is appropriate
        self.setpout = self.checkentriescorrect(self.entries) 
        if self.setpout == False: 
            self.lockentries("enabled",basicdata.lockedentries,basicdata.lockedbuttons)
            return
        # checking there's no missing keys
        for item in basicdata.requiredkeys: 
            if item not in list(self.setpout.keys()): 
                self.messageprint(item+" is a required value.\n")
                self.lockentries("enabled",basicdata.lockedentries,basicdata.lockedbuttons)
                return
        # check that the wire is in an ok position
        temppos = float(self.readbacks[basicdata.pdict[self.setpout["Wire"]][0]].get())
        if temppos <= self.setpout["Out Limit"]: 
            self.setpout["Direction"] = 0 # 0 for going in, 1 for going out
        elif temppos >= self.setpout["In Limit"]: 
            self.setpout["Direction"] = 1
        else: 
            self.messageprint(basicdata.pdict[self.setpout["Wire"]][0]+" is not outside In/Out Limit.\n")
            self.lockentries("enabled",basicdata.lockedentries,basicdata.lockedbuttons)
            return
        # add new frame with additional readbacks
        self.addparampopup(frame14,self.setpout["Additional Parameters"])              
        
        # things that doesn't need to be saved in setup parameters (some still are) but needs to be accessible by scan
        self.setpout["Timestamp"] = round(time.time()) # choose unix time stamp around now 
        # make directory
        savepath = os.path.join(self.setpout["Save Directory"],str(self.setpout["Timestamp"])+"_"+self.setpout["Wire"]).replace("\\","/")
        if not os.path.exists(savepath): 
            os.makedirs(savepath)
            self.setpout["WS Directory"] = savepath
        else: 
            self.messageprint("Folder for data unable to be created.\n")
            self.lockentries("enabled",basicdata.lockedentries,basicdata.lockedbuttons)
            return
        basicfuncs.dicttojson(self.setpout,os.path.join(self.setpout["WS Directory"],"_".join([str(self.setpout["Timestamp"]),self.setpout["Wire"],"SetupParameters.json"])))
        # make dict of tags
        tagdict, i = {}, 1
        for device in basicdata.pdict[self.setpout['Wire']]+basicdata.sdict[self.setpout['Wire']]+self.setpout['Additional Parameters']:
            tagdict[i]=device
            i=i+1
        self.setpout["Tags"] = tagdict

        # collect metadata 
        self.metad = {key:self.setpout[key] for key in ['Event', 'User Comment','Timestamp','WS Directory','Direction','Tags']}
        if self.setpout["Event"] == "0A": 
            params = ["L:SOURCE.READING","L:D7TOR.READING","L:TCHTON.READING","L:TCHTOF.READING","L:BSTUDY.READING"]
        else: 
            params = ["L:SOURCE.READING","L:D7TOR.READING"]
        m = self.acsyscontrol.checkparam(params,10)
        if m[0] == -10.24:
            self.metad["Source"] = "A"
        elif m[0] == 10.24: 
            self.metad["Source"] = "B"
        self.metad["L:D7TOR"] = m[1]
        if len(params) == 5: 
            self.metad["Pulse Length"] = m[3]-m[2]
            self.metad["Frequency"] = m[4]
        self.metad["Abort"] = False
        basicfuncs.dicttojson(self.metad,os.path.join(self.setpout["WS Directory"],"_".join([str(self.setpout["Timestamp"]),self.setpout["Wire"],"Metadata.json"])))
        
        # start wirescan 
        self.plot_thread = "liveplot" 
        self.acsyscontrol.start_scan_thread(self.scan_thread,self.setpout,self.lockentries,self.messageprint,self.plot_thread)
        self.messageprint("Scan initiated.\n")
        # start plotting here
        if self.plot_thread in self.acsyscontrol.get_list_of_threads(): 
            self.acsyscontrol.end_any_thread(self.plot_thread)
        print("Starting liveplot")
        self.acsyscontrol.start_liveplot_thread(self.plot_thread,self.scan_thread,self.setpout["Wire"],self.plotobjects1)

    def abortbutton(self): 
        """Abort an ongoing scan."""
        try: 
            if self.scan_thread in self.acsyscontrol.get_list_of_threads(): # kill existing thread if present
                self.acsyscontrol.end_any_thread(self.scan_thread)
                self.messageprint("Scan aborted by user.\n") 
                self.wiresout() # think more about this
                # record that an abort occurred by editing the metadata file
                self.metad["Abort"] = True
                basicfuncs.dicttojson(self.metad,os.path.join(self.setpout["WS Directory"],"_".join([str(self.setpout["Timestamp"]),self.setpout["Wire"],"Metadata.json"])))
            else: 
                self.messageprint("No scan to abort.\n")
        except AttributeError: 
            self.messageprint("No scan to abort.\n") 

    def wiresout(self):
        """Issue setting to move wire to the out position."""
        if self.entries["Wire"].get().strip() in basicdata.pdict.keys():
            try: 
                self.acsyscontrol.setparam(basicdata.pdict[self.entries["Wire"].get().strip()][0],-12700)
                self.messageprint("Out setting issued to "+basicdata.pdict[self.entries["Wire"].get().strip()][0]+".\n")
            except ValueError:
                self.messageprint("Invalid Kerberos realm.\n") 
        else: 
            self.messageprint("No wire selected, cannot pull wire out.\n")

if __name__ == "__main__":
    app = QuadScanApp()
    app.mainloop()