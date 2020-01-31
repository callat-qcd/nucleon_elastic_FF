import numpy as np

def getLineInfo(l):
    #PBP: mass 6.730000e-02     tslice 14 1.754393e-03  1.786215e-03  -2.306500e-05  -1.151786e-04 ( 6 of 200 )
    line=l.split()
    tsum=None
    if 'PBP:' and 'tslice' in line:
        #mass,tslice,valEven,valOdd,npbp=float(line[2]),int(line[4]),float(line[5]),float(line[6]),int(line[-4])
        mass,tslice,valEven,valOdd,valEvenIm,valOddIm,npbp=float(line[2]),int(line[4]),\
                                          float(line[5]),float(line[6]),float(line[7]),float(line[8]),int(line[-4])
    else:
        mass,tslice,valEven,valOdd,valEvenIm,valOddIm,npbp=None,None,None,None,None,None,None
        if 'PBP:' in line:
            mass,tsum,npbp=float(line[2]),[float(line[3]),float(line[4])],int(line[-4])

            #print 'tsum',tsum
    return mass,tslice,valEven,valOdd,valEvenIm,valOddIm,tsum,npbp

def getLoopDataTextFromFile(fname):
	text=open(fname).read()

	if 'RUNNING COMPLETED' not in text:
		int('c')
	newSetLine='Turning ON boundary phases 0 0 0 0 to FN links r0 0 0 0 0'
	npbpEndLine='new npbp or new mass'

	#Split into measurement sets
	setSplitText=text.split(newSetLine)[1::]
	dataSets,set_npbp=[],[]
	for i,iset in enumerate(setSplitText):
		tempText=''
		for x in iset.split('\n'):
			if 'PBP: mass ' in x:
				tempText+=x+'\n'
			if 'FACTION: mass =' in x:
				tempText+=npbpEndLine+'\n'

		tempSet=tempText.split(npbpEndLine)[0:-1]
		set_npbp.append(int(tempSet[0].split()[-2]))

		if len(tempSet) != set_npbp[i]:
			inds=[]
			for j in range(len(tempSet)/set_npbp[i]):
				inds.append(np.arange(0+j,len(tempSet),len(tempSet)/set_npbp[i]))
				dataSets.append(np.array(tempSet)[inds[j]])
		else:
			dataSets.append(np.array(tempSet))

	return dataSets,set_npbp

def getLoopData(dataSets,NT):
	data,dataSum=[],[]
	for i in range(len(dataSets)):	
		data.append(np.zeros(shape=(dataSets[i].shape[0],NT,4)))
		dataSum.append(np.zeros(shape=(dataSets[i].shape[0],2)))
		for nTex in dataSets[i]:
			for k,l in enumerate(nTex.split('\n')):
                                #mass,tslice,valEven,valOdd,valEvenIm,valOddIm,tsum,npbp
				#lmass,tsl,valEven,valOdd,ltsum,npbp=getLineInfo(l)
                                lmass,tsl,valEven,valOdd,valEvenIm,valOddIm,ltsum,npbp=getLineInfo(l)
			        #print l,'\n',lmass,tsl,valEven,valOdd,ltsum,npbp
				if tsl is not None:
					#data[i][npbp-1][tsl]=float(valEven)
                                        data[i][npbp-1][tsl]=np.array([valEven,valOdd,valEvenIm,valOddIm])
				else:
					if l!='':
						#print i,npbp-1, len(dataSum)
						dataSum[i][npbp-1]=np.array(ltsum)

			#print

	return data,dataSum
