import numpy as np
import pyqtgraph as pg
import time
import csv

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time

from lantz.drivers.stanford.srs900 import SRS900
from lantz.drivers.qutools import QuTAG

class PhotonCount(Spyrelet):
	requires = {
    	'srs': SRS900
    }
	qutag = None
	currents=[]
	efficiencies=[]

	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@qutagInit.initializer
	def initialize(self):
		from lantz.drivers.qutools import QuTAG
		self.qutag = QuTAG()
		devType = self.qutag.getDeviceType()
		if (devType == self.qutag.DEVTYPE_QUTAG):
			print("found quTAG!")
		else:
			print("no suitable device found - demo mode activated")
		print("Device timebase:" + str(self.qutag.getTimebase()))
		return

	@qutagInit.finalizer
	def finalize(self):
		return
	

	@Task()
	def getPhotonCounts(self):
		#self.srs.SIM928_voltage[5]=0
		self.srs.SIM928_voltage[5]=0
		self.srs.module_reset[5]
		#self.srs.module_reset[5]
		self.srs.wait_time(100000)
		qutagparams = self.qutag_params.widget.get()
		start = qutagparams['Start Channel']
		stop_1 = qutagparams['Stop Channel 1']
		#stop_2 = qutagparams['Stop Channel 2']
        ##True = rising edge, False = falling edge. Final value is threshold voltage
		self.qutag.setSignalConditioning(start,self.qutag.SIGNALCOND_MISC,True,0.1)
		self.qutag.setSignalConditioning(stop_1,self.qutag.SIGNALCOND_MISC,True,0.1)
		self.qutag.enableChannels((start,stop_1))
		biasCurrentParams = self.bias_current.widget.get()
		qutagParams = self.qutag_params.widget.get()
		resistance = 10000
		startCurrent = biasCurrentParams['Start Current'].to('A').magnitude
		stepSize = biasCurrentParams['Step Size'].to('A').magnitude
		stopCurrent = biasCurrentParams['Stop Current'].to('A').magnitude
		print('start current is' + str(startCurrent))
		print('step size is' + str(stepSize))
		print('stop current is'+ str(stopCurrent))
		expParams = self.exp_params.widget.get()
		currentCurrent = startCurrent
		self.srs.SIM928_voltage[5] = currentCurrent*resistance
		self.srs.SIM928_on[5]
		self.srs.wait_time(100000)
		points = ((stopCurrent-startCurrent)/stepSize)+(1+stepSize)
		print(points)
		BC =[]
		PCR_1 =[]
		for i in range(int(points)):
			lost = self.qutag.getLastTimestamps(True)
			time.sleep(expParams['Exposure Time'].magnitude)
			timestamps = self.qutag.getLastTimestamps(True)
			tstamp = timestamps[0] # array of timestamps
			tchannel = timestamps[1] # array of channels
			values = timestamps[2] # number of recorded timestamps
			photoncounts = values
			BC.append(currentCurrent)
			self.currents.append(currentCurrent*resistance)
			PCR_1.append(photoncounts/expParams['Exposure Time'].magnitude)
			self.darkcountspercurrent.append(photoncounts/expParams['Exposure Time'].magnitude)
			currentCurrent += stepSize
			self.srs.SIM928_voltage[5] = currentCurrent*resistance
			values = {
					'bc': self.currents,
					'dc': self.efficiencies,
			}
		self.srs.SIM928_voltage[5]=0
		self.srs.module_reset[5]
		datadir = 'D:\Data\\09.09.2019\\'
		np.savetxt(datadir+expParams['File Name']+'SNSPD2'+'.csv', (BC,PCR_1), delimiter=',')
		print('Data stored under File Name: ' + expParams['File Name'] + 'SNSPD2')	
		return



	@Element(name = 'Bias Current')
	def bias_current(self):
		params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Start Current', {'type': float, 'default': 2, 'units': 'uA'}),
        ('Step Size', {'type': float, 'default': 0.2, 'units': 'uA'}),
        ('Stop Current', {'type': float, 'default': 10, 'units': 'uA'})
        ]
		w = ParamWidget(params)
		return w

	@Element(name = 'Experimental Parameters')
	def exp_params(self):
		params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Exposure Time', {'type': int, 'default': 10, 'units': 's'}),
        ('Points per Bias Current',{'type':int, 'default': 1.0}),
        ('File Name', {'type': str})
        ]
		w = ParamWidget(params)
		return w


	@getPhotonCounts.initializer
	def initialize(self):
		print('The identification of this instrument is : ' + self.srs.idn)
		print(self.srs.self_test)
		return

	@getPhotonCounts.finalizer
	def finalize(self):
		return

	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel 1', {'type': int, 'default': 1}),
		('Stop Channel 2', {'type': int, 'default': 2})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Histogram')
	def photoncountsplot(self):
		p=LinePlotWidget()
		p.plot('Photon Counts vs. Bias Current')
		return p

	@photoncountsplot.on(getPhotonCounts.acquired)
	def photoncountsplot_update(self, ev):
		w=ev.widget
		bc=np.array(self.currents)
		cs=np.array(self.efficiencies)
		w.set('Dark Counts vs. Bias Current', xs=bc, ys=cs)
		return


