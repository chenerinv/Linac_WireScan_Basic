import new_basicfuncs as basicfuncs
import matplotlib.pyplot as plt
import numpy as np

q01_q02 = 1.535
q02_q03 = 1.037
q03_q04 = 0.730
q04_q11 = 1.640
q11_q12 = 1.684
q02_d02 = 0.003
q03_d03 = 0.068
q04_d12 = 3.390
q12_d12 = 0.066

### needed values
q1currents = [50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165] # amps
q2currents = [50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165] # amps
q3currents = [50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165]
q4currents = [126.9]
defocusing = [1,3] # which if any quads are defocusing
d12 = q03_q04 # m 
d23 = q04_q11 # m 
d34 = q11_q12 # m 
d4screen = q12_d12 # m
energy = 116.5 # MeV

###

gamma = energy/939.292+1
beta = np.sqrt(1-1/gamma**2)

k1, k2, k3, k4 = 1,1,1,1
if 1 in defocusing: k1 = -1
elif 2 in defocusing: k2 = -1
elif 3 in defocusing: k3 = -1
elif 4 in defocusing: k4 = -1

kl1s = [basicfuncs.currtokl(x,beta,energy)*k1 for x in q1currents]
kl2s = [basicfuncs.currtokl(x,beta,energy)*k2 for x in q2currents]
kl3s = [basicfuncs.currtokl(x,beta,energy)*k3 for x in q3currents]
kl4s = [basicfuncs.currtokl(x,beta,energy)*k4 for x in q4currents]
d1 = d12
d2 = d23
d3 = d34
d4 = d4screen

angles, ss = [], []
k1s, k2s, k3s, k4s = [],[],[],[]

for i,kl1 in enumerate(kl1s): 
    for j,kl2 in enumerate(kl2s):
        for k,kl3 in enumerate(kl3s): 
            for l,kl4 in enumerate(kl4s): 
                m11 = kl1*(d2*(d4*kl4 + kl3*(d4 - d3*(d4*kl4 - 1)) - 1) - d4 + d3*(d4*kl4 - 1) + d1*(d4*kl4 - kl2*(d2*(d4*kl4 + kl3*(d4 - d3*(d4*kl4 - 1)) - 1) - d4 + d3*(d4*kl4 - 1)) + kl3*(d4 - d3*(d4*kl4 - 1)) - 1)) - d4*kl4 + kl2*(d2*(d4*kl4 + kl3*(d4 - d3*(d4*kl4 - 1)) - 1) - d4 + d3*(d4*kl4 - 1)) - kl3*(d4 - d3*(d4*kl4 - 1)) + 1
                m12 = d4 - d2*(d4*kl4 + kl3*(d4 - d3*(d4*kl4 - 1)) - 1) - d3*(d4*kl4 - 1) - d1*(d4*kl4 - kl2*(d2*(d4*kl4 + kl3*(d4 - d3*(d4*kl4 - 1)) - 1) - d4 + d3*(d4*kl4 - 1)) + kl3*(d4 - d3*(d4*kl4 - 1)) - 1)
                angles.append(np.rad2deg(np.arctan(m12/m11)))
                ss.append(np.sqrt(m11**2+m12**2))
                k1s.append(q1currents[i])
                k2s.append(q2currents[j])
                k3s.append(q3currents[k])
                k4s.append(q4currents[l])

print(min(angles),max(angles))

ss = [x for _, x in sorted(zip(angles,ss))]
k1s = [x for _, x in sorted(zip(angles,k1s))]
k2s = [x for _, x in sorted(zip(angles,k2s))]
k3s = [x for _, x in sorted(zip(angles,k3s))]
k4s = [x for _, x in sorted(zip(angles,k4s))]
angles.sort()

exportdict = {"Angle": angles, "Scaling": ss, "Current1": k1s, "Current2": k2s,"Current3":k3s,"Current4":k4s}
basicfuncs.dicttocsv(exportdict,"TomogTestV_M01.csv")

plt.figure()
plt.scatter(angles,np.zeros(len(angles)),label="Phase Space Rotation Angle")
plt.scatter(angles,k1s,marker=".",alpha=0.5,label="kl1")
plt.scatter(angles,k2s,marker=".",alpha=0.5,label="kl2")
plt.scatter(angles,k3s,marker=".",alpha=0.5,label="kl3")
#plt.scatter(angles,k4s,marker=".",alpha=0.5,label="kl4")
plt.legend()
plt.xlim([-90,90])
plt.savefig("TomogTestV_M01.png")
plt.show()