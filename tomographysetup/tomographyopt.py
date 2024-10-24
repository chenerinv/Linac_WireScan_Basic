import new_basicfuncs as basicfuncs

### inputs
#goals = [57.11, 84.63, 112.8, 120.3] # M0
goals = [112.8, 120.3, 114, 126.9] # M01
###

def closest2nom(importdict,limits,c1goal,c2goal,c3goal,c4goal):
    # finding the best score
    bestscore = [500000]
    bestind = [-1]
    for i,angle in enumerate(importdict["Angle"]): 
        if (angle < max(limits)) and (angle > min(limits)):
            a=abs(importdict["Current1"][i]-c1goal)
            b=abs(importdict["Current2"][i]-c2goal)
            c=abs(importdict["Current3"][i]-c3goal)
            d=abs(importdict["Current4"][i]-c4goal)
            score = a+b+c+d
            if score < bestscore[0]: 
                bestscore = [score]
                bestind = [i]
            elif score == bestscore[0]: 
                bestscore.append(score)
                bestind.append(i)
    for i,j in enumerate(bestind):
        print(bestscore[i], j, importdict["Angle"][j],importdict["Current1"][j],importdict["Current2"][j],importdict["Current3"][j],importdict["Current4"][j])

tomogdict = basicfuncs.csvtodict("TomogTestV_M01.csv")

for i in range(-90,90,5):
    print(i)
    closest2nom(tomogdict,[i,i+5],*goals)

print(len(range(-90,90,5)))    


