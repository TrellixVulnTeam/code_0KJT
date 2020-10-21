import numpy as np
import pyqtgraph as pg
import time
import csv
import os

from PyQt5.Qsci import QsciScintilla, QsciLexerPython
import matplotlib.pyplot as plt

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time

from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford import DG645
from lantz.drivers.tektronix import TDS5104
from lantz.drivers.keysight import N5181A
from lantz.drivers.tektronix import TDS5104
from lantz.log import log_to_screen, DEBUG


volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')

class Record(Spyrelet):

	requires = {
		'osc': TDS5104,
		'delaygen': DG645,
		'source':N5181A,
		'fungen': Keysight_33622A,
	}


	def record(self,tau,ndelay):
# Set the AWG 
		self.dataset.clear()
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)

		self.fungen.wait()

		params = self.pulse_parameters.widget.get()
		repeatmag=params['dc repeat unit'].magnitude
		timestep=params['timestep'].magnitude
		npulses=params['nPulses'].magnitude
		pulsewidth=params['pulse width'].magnitude
		naverage=params['nAverage'].magnitude
		# nmeasurement=params['nMeasurement'].magnitude						
		freq=params['IQFrequency'].magnitude
		phase=params['Phase'].magnitude
		cavityfreq=params['CavityFreq'].magnitude
		trigperiod=params['period'].magnitude
		triggerdelay=params['trigger delay'].magnitude
		Amp_factor_pi2=params['Pi2factor'].magnitude
		deltaphiiq=93  # Based off calibration
		predelay=50e-9
		postdelay=150e-9

		deltaphase1=0  #X
		deltaphase2=90 #Y
		deltaphase3=180 #-X
		deltaphase4=270 #-Y

# Waves for Spin Echo
		Wavepi2pulse='Square'   # 'Gaussian' or 'Square'
		Wavepipulse='Square'


# Triggering delay

		delay0I = Arbseq_Class_MW('delay0I', timestep,'DC',0,triggerdelay,0,0)
		repeatwidthdelay0I=(triggerdelay)
		delay0I.setRepeats(repeatwidthdelay0I)
		delay0I.create_envelope()
		delay0I.repeatstring = 'onceWaitTrig'
		# delay0I.sendTrigger()

		delay0Q = Arbseq_Class_MW('delay0Q', timestep,'DC',0,triggerdelay,0,0)
		repeatwidthdelay0Q=(triggerdelay)
		delay0Q.setRepeats(repeatwidthdelay0Q)
		delay0Q.repeatstring = 'onceWaitTrig'
		delay0Q.create_envelope()

# Pi/2x pulse

		pi2xPulseI = Arbseq_Class_MW('pi2xPulseI', timestep,Wavepi2pulse,Amp_factor_pi2,pulsewidth,freq,phase+deltaphase1)
		pi2xPulseI.delays=predelay
		pi2xPulseI.postdelay=postdelay
		pi2xPulseI.sendTrigger()
		pi2xPulseI.create_envelope()

		pi2xPulseQ = Arbseq_Class_MW('pi2xPulseQ', timestep,Wavepi2pulse,Amp_factor_pi2,pulsewidth,freq,phase+deltaphiiq+deltaphase1)
		pi2xPulseQ.delays=predelay
		pi2xPulseQ.postdelay=postdelay		
		pi2xPulseQ.create_envelope()

# Pi/2y pulse

		pi2yPulseI = Arbseq_Class_MW('pi2yPulseI', timestep,Wavepi2pulse,Amp_factor_pi2,pulsewidth,freq,phase+deltaphase2)
		pi2yPulseI.delays=predelay
		pi2yPulseI.postdelay=postdelay
		pi2yPulseI.sendTrigger()
		pi2yPulseI.create_envelope()

		pi2yPulseQ = Arbseq_Class_MW('pi2yPulseQ', timestep,Wavepi2pulse,Amp_factor_pi2,pulsewidth,freq,phase+deltaphiiq+deltaphase2)
		pi2yPulseQ.delays=predelay
		pi2yPulseQ.postdelay=postdelay		
		pi2yPulseQ.create_envelope()


# Pi/2mx pulse

		pi2mxPulseI = Arbseq_Class_MW('pi2mxPulseI', timestep,Wavepi2pulse,Amp_factor_pi2,pulsewidth,freq,phase+deltaphase3)
		pi2mxPulseI.delays=predelay
		pi2mxPulseI.postdelay=postdelay
		pi2mxPulseI.sendTrigger()
		pi2mxPulseI.create_envelope()

		pi2mxPulseQ = Arbseq_Class_MW('pi2mxPulseQ', timestep,Wavepi2pulse,Amp_factor_pi2,pulsewidth,freq,phase+deltaphiiq+deltaphase3)
		pi2mxPulseQ.delays=predelay
		pi2mxPulseQ.postdelay=postdelay		
		pi2mxPulseQ.create_envelope()

# Pi/2my pulse

		pi2myPulseI = Arbseq_Class_MW('pi2myPulseI', timestep,Wavepi2pulse,Amp_factor_pi2,pulsewidth,freq,phase+deltaphase4)
		pi2myPulseI.delays=predelay
		pi2myPulseI.postdelay=postdelay
		pi2myPulseI.sendTrigger()
		pi2myPulseI.create_envelope()

		pi2myPulseQ = Arbseq_Class_MW('pi2myPulseQ', timestep,Wavepi2pulse,Amp_factor_pi2,pulsewidth,freq,phase+deltaphiiq+deltaphase4)
		pi2myPulseQ.delays=predelay
		pi2myPulseQ.postdelay=postdelay		
		pi2myPulseQ.create_envelope()



# Delay of Tau

		delay1 = Arbseq_Class_MW('delay1', timestep,'DC',0,repeatmag,0,0)
		repeatwidthdelay1=(tau-1.0*pulsewidth-predelay-postdelay)
		delay1.setRepeats(repeatwidthdelay1)
		delay1.create_envelope()

# Pix Pulse

		pixPulseI = Arbseq_Class_MW('pixPulseI', timestep,Wavepipulse,0.08,pulsewidth,freq,phase+deltaphase1)
		pixPulseI.delays=predelay
		pixPulseI.postdelay=postdelay
		pixPulseI.sendTrigger()
		pixPulseI.create_envelope()


		pixPulseQ = Arbseq_Class_MW('pixPulseQ', timestep,Wavepipulse,0.08,pulsewidth,freq,phase+deltaphase1+deltaphiiq)
		pixPulseQ.delays=predelay
		pixPulseQ.postdelay=postdelay		
		pixPulseQ.create_envelope()

# Piy Pulse

		piyPulseI = Arbseq_Class_MW('piyPulseI', timestep,Wavepipulse,0.08,pulsewidth,freq,phase+deltaphase2)
		piyPulseI.delays=predelay
		piyPulseI.postdelay=postdelay
		piyPulseI.sendTrigger()
		piyPulseI.create_envelope()


		piyPulseQ = Arbseq_Class_MW('piyPulseQ', timestep,Wavepipulse,0.08,pulsewidth,freq,phase+deltaphase2+deltaphiiq)
		piyPulseQ.delays=predelay
		piyPulseQ.postdelay=postdelay		
		piyPulseQ.create_envelope()


# Pimx Pulse

		pimxPulseI = Arbseq_Class_MW('pimxPulseI', timestep,Wavepipulse,0.08,pulsewidth,freq,phase+deltaphase3)
		pimxPulseI.delays=predelay
		pimxPulseI.postdelay=postdelay
		pimxPulseI.sendTrigger()
		pimxPulseI.create_envelope()


		pimxPulseQ = Arbseq_Class_MW('pimxPulseQ', timestep,Wavepipulse,0.08,pulsewidth,freq,phase+deltaphase3+deltaphiiq)
		pimxPulseQ.delays=predelay
		pimxPulseQ.postdelay=postdelay		
		pimxPulseQ.create_envelope()

# Pimy Pulse

		pimyPulseI = Arbseq_Class_MW('pimyPulseI', timestep,Wavepipulse,0.08,pulsewidth,freq,phase+deltaphase4)
		pimyPulseI.delays=predelay
		pimyPulseI.postdelay=postdelay
		pimyPulseI.sendTrigger()
		pimyPulseI.create_envelope()


		pimyPulseQ = Arbseq_Class_MW('pimyPulseQ', timestep,Wavepipulse,0.08,pulsewidth,freq,phase+deltaphase4+deltaphiiq)
		pimyPulseQ.delays=predelay
		pimyPulseQ.postdelay=postdelay		
		pimyPulseQ.create_envelope()


# COMP1 Pulse (pi/2x pi/2my)

		COMP1PulseI = Arbseq_Class_MW('COMP1PulseI', timestep,'COMP1',0.08,pulsewidth,freq,phase)
		COMP1PulseI.delays=predelay
		COMP1PulseI.postdelay=postdelay
		COMP1PulseI.sendTrigger()
		COMP1PulseI.create_envelope()


		COMP1PulseQ = Arbseq_Class_MW('COMP1PulseQ', timestep,'COMP1',0.08,pulsewidth,freq,phase+deltaphiiq)
		COMP1PulseQ.delays=predelay
		COMP1PulseQ.postdelay=postdelay		
		COMP1PulseQ.create_envelope()


# COMP2 Pulse (pi/2my pi/2x)

		COMP2PulseI = Arbseq_Class_MW('COMP2PulseI', timestep,'COMP2',0.08,pulsewidth,freq,phase)
		COMP2PulseI.delays=predelay
		COMP2PulseI.postdelay=postdelay
		COMP2PulseI.sendTrigger()
		COMP2PulseI.create_envelope()


		COMP2PulseQ = Arbseq_Class_MW('COMP2PulseQ', timestep,'COMP2',0.08,pulsewidth,freq,phase+deltaphiiq)
		COMP2PulseQ.delays=predelay
		COMP2PulseQ.postdelay=postdelay		
		COMP2PulseQ.create_envelope()


# COMP3 Pulse (pi/2x pi/2y)

		COMP3PulseI = Arbseq_Class_MW('COMP3PulseI', timestep,'COMP3',0.08,pulsewidth,freq,phase)
		COMP3PulseI.delays=predelay
		COMP3PulseI.postdelay=postdelay
		COMP3PulseI.sendTrigger()
		COMP3PulseI.create_envelope()


		COMP3PulseQ = Arbseq_Class_MW('COMP3PulseQ', timestep,'COMP3',0.08,pulsewidth,freq,phase+deltaphiiq)
		COMP3PulseQ.delays=predelay
		COMP3PulseQ.postdelay=postdelay		
		COMP3PulseQ.create_envelope()


# COMP4 Pulse (pi/2x pi/2y)

		COMP4PulseI = Arbseq_Class_MW('COMP4PulseI', timestep,'COMP4',0.08,pulsewidth,freq,phase)
		COMP4PulseI.delays=predelay
		COMP4PulseI.postdelay=postdelay
		COMP4PulseI.sendTrigger()
		COMP4PulseI.create_envelope()


		COMP4PulseQ = Arbseq_Class_MW('COMP4PulseQ', timestep,'COMP4',0.08,pulsewidth,freq,phase+deltaphiiq)
		COMP4PulseQ.delays=predelay
		COMP4PulseQ.postdelay=postdelay		
		COMP4PulseQ.create_envelope()



# Delay of 2 tau

		delay2 = Arbseq_Class_MW('delay2', timestep,'DC',0,repeatmag,0,0) #Block for 2 tau
		repeatwidthdelay2=(2*tau-pulsewidth-predelay-postdelay)
		delay2.setRepeats(repeatwidthdelay2)
		delay2.create_envelope()


# Send all the Arbs


		self.fungen.send_arb(delay0I, 1)
		self.fungen.send_arb(pi2xPulseI, 1)
		self.fungen.send_arb(pi2yPulseI, 1)		
		self.fungen.send_arb(pi2mxPulseI, 1)
		self.fungen.send_arb(pi2myPulseI, 1)	
		self.fungen.send_arb(delay1, 1)
		self.fungen.send_arb(delay2, 1)
		self.fungen.send_arb(pixPulseI, 1)
		self.fungen.send_arb(piyPulseI, 1)
		self.fungen.send_arb(pimyPulseI, 1)
		self.fungen.send_arb(pimxPulseI, 1)
		self.fungen.send_arb(COMP1PulseI, 1)
		self.fungen.send_arb(COMP2PulseI, 1)
		self.fungen.send_arb(COMP3PulseI, 1)
		self.fungen.send_arb(COMP4PulseI, 1)


		self.fungen.send_arb(delay0Q, 2)
		self.fungen.send_arb(pi2xPulseQ, 2)
		self.fungen.send_arb(pi2yPulseQ, 2)		
		self.fungen.send_arb(pi2mxPulseQ, 2)
		self.fungen.send_arb(pi2myPulseQ, 2)	
		self.fungen.send_arb(delay1, 2)
		self.fungen.send_arb(delay2, 2)
		self.fungen.send_arb(pixPulseQ, 2)
		self.fungen.send_arb(piyPulseQ, 2)
		self.fungen.send_arb(pimyPulseQ, 2)
		self.fungen.send_arb(pimxPulseQ, 2)
		self.fungen.send_arb(COMP1PulseQ, 2)
		self.fungen.send_arb(COMP2PulseQ, 2)
		self.fungen.send_arb(COMP3PulseQ, 2)
		self.fungen.send_arb(COMP4PulseQ, 2)



# Make sequence

		seq = [delay0I,pi2xPulseI, delay1]

		seq1 = [delay0Q ,pi2xPulseQ, delay1]

		for i in range(0,npulses):

#First channel

#1
			seq.append(pixPulseI)   #Pix
			seq.append(delay2)

			seq.append(COMP1PulseI)   #Pi2x, Pi2my
			seq.append(delay2)

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

			seq.append(pixPulseI)   #Pix
			seq.append(delay2)
#2

			seq.append(COMP1PulseI)   #Pi2x, Pi2my
			seq.append(delay2)

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

			seq.append(pixPulseI)   #Pix
			seq.append(delay2)

			seq.append(COMP1PulseI)   #Pi2x, Pi2my
			seq.append(delay2)

#3

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

			seq.append(pimyPulseI)   #Pimy
			seq.append(delay2)	

			seq.append(COMP2PulseI)   #Pi2my, Pi2x
			seq.append(delay2)

#4

			seq.append(piyPulseI)   #Piy
			seq.append(delay2)

			seq.append(piyPulseI)   #Piy
			seq.append(delay2)

			seq.append(pimyPulseI)   #Pimy
			seq.append(delay2)	

			seq.append(COMP2PulseI)   #Pi2my, Pi2x
			seq.append(delay2)

			seq.append(piyPulseI)   #Piy
			seq.append(delay2)

			seq.append(piyPulseI)   #Piy
			seq.append(delay2)

#5


			seq.append(pimyPulseI)   #Pimy
			seq.append(delay2)	

			seq.append(COMP2PulseI)   #Pi2my, Pi2x
			seq.append(delay2)

			seq.append(piyPulseI)   #Piy
			seq.append(delay2)


			seq.append(piyPulseI)   #Piy
			seq.append(delay2)

			seq.append(pimyPulseI)   #Pimy
			seq.append(delay2)

#6	

			seq.append(COMP3PulseI)   #Pi2x, Pi2y
			seq.append(delay2)

			seq.append(piyPulseI)   #Piy
			seq.append(delay2)

			seq.append(pimyPulseI)   #Pimy
			seq.append(delay2)

			seq.append(pimyPulseI)   #Pimy
			seq.append(delay2)

			seq.append(COMP3PulseI)   #Pi2x, Pi2y
			seq.append(delay2)

#7

			seq.append(piyPulseI)   #Piy
			seq.append(delay2)

			seq.append(pimyPulseI)   #Pimy
			seq.append(delay2)

			seq.append(pimyPulseI)   #Pimy
			seq.append(delay2)

			seq.append(COMP3PulseI)   #Pi2x, Pi2y
			seq.append(delay2)

			seq.append(piyPulseI)   #Piy
			seq.append(delay2)


#8

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

			seq.append(COMP4PulseI)   #Pi2y, Pi2x
			seq.append(delay2)

			seq.append(pixPulseI)   #Pix
			seq.append(delay2)

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

#9


			seq.append(COMP4PulseI)   #Pi2y, Pi2x
			seq.append(delay2)

			seq.append(pixPulseI)   #Pix
			seq.append(delay2)

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

			seq.append(pimxPulseI)   #Pimx
			seq.append(delay2)

			seq.append(COMP4PulseI)   #Pi2y, Pi2x
			seq.append(delay2)

			seq.append(pixPulseI)   #Pix
			seq.append(delay2)

			seq.append(pimyPulseI)   #Pimy
			seq.append(delay2)




# Second channel

			seq1.append(pixPulseQ)  #Pix
			seq1.append(delay2)

			seq1.append(COMP1PulseQ)   #Pi2x, Pi2my
			seq1.append(delay2)

			seq1.append(pimxPulseQ)   #Pimx
			seq1.append(delay2)

			seq1.append(pi2mxPulseQ)   #Pimx
			seq1.append(delay2)

			seq1.append(pixPulseQ)  #Pix
			seq1.append(delay2)

			seq1.append(COMP1PulseQ)   #Pi2x, Pi2my
			seq1.append(delay2)

			seq1.append(pimxPulseQ)   #Pimx
			seq1.append(delay2)

			seq1.append(pimxPulseQ)   #Pimx
			seq1.append(delay2)

			seq1.append(pixPulseQ)  #Pix
			seq1.append(delay2)

			seq1.append(COMP1PulseQ)   #Pi2x, Pi2my
			seq1.append(delay2)

			seq1.append(pimxPulseQ)   #Pimx
			seq1.append(delay2)

			seq1.append(pimxPulseQ)   #Pimx
			seq1.append(delay2)

			seq1.append(pimyPulseQ)   #Pimy
			seq1.append(delay2)


			seq1.append(COMP2PulseQ)   #Pi2my, Pi2x
			seq1.append(delay2)

			seq1.append(piyPulseQ)  #Piy
			seq1.append(delay2)

			seq1.append(piyPulseQ)  #Piy
			seq1.append(delay2)

			seq1.append(pimyPulseQ)   #Pimy
			seq1.append(delay2)

			seq1.append(COMP2PulseQ)   #Pi2my, Pi2x
			seq1.append(delay2)

			seq1.append(piyPulseQ)  #Piy
			seq1.append(delay2)

			seq1.append(piyPulseQ)  #Piy
			seq1.append(delay2)

			seq1.append(pimyPulseQ)   #Pimy
			seq1.append(delay2)

			seq1.append(COMP2PulseQ)   #Pi2my, Pi2x
			seq1.append(delay2)

			seq1.append(piyPulseQ)  #Piy
			seq1.append(delay2)

			seq1.append(piyPulseQ)  #Piy
			seq1.append(delay2)

			seq1.append(pimyPulseQ)   #Pimy
			seq1.append(delay2)

			seq1.append(COMP3PulseQ)   #Pi2x, Pi2y
			seq1.append(delay2)

			seq1.append(piyPulseQ)  #Piy
			seq1.append(delay2)

			seq1.append(pimyPulseQ)   #Pimy
			seq1.append(delay2)

			seq1.append(pimyPulseQ)   #Pimy
			seq1.append(delay2)

			seq1.append(COMP3PulseQ)   #Pi2x, Pi2y
			seq1.append(delay2)

			seq1.append(piyPulseQ)  #Piy
			seq1.append(delay2)


			seq1.append(pimyPulseQ)   #Pimy
			seq1.append(delay2)

			seq1.append(pimyPulseQ)   #Pimy
			seq1.append(delay2)

			seq1.append(COMP3PulseQ)   #Pi2x, Pi2y
			seq1.append(delay2)

			seq1.append(piyPulseQ)  #Piy
			seq1.append(delay2)


			seq1.append(pimxPulseQ)   #Pimx
			seq1.append(delay2)

			seq1.append(pimxPulseQ)   #Pimx
			seq1.append(delay2)

			seq1.append(COMP4PulseQ)   #Pi2y, Pi2x
			seq1.append(delay2)

			seq1.append(pixPulseQ)  #Pix
			seq1.append(delay2)

			seq1.append(pimxPulseQ)   #Pimx
			seq1.append(delay2)

			seq1.append(pimxPulseQ)   #Pimx
			seq1.append(delay2)


			seq1.append(COMP4PulseQ)   #Pi2y, Pi2x
			seq1.append(delay2)

			seq1.append(pixPulseQ)  #Pix
			seq1.append(delay2)

			seq1.append(pimxPulseQ)   #Pimx
			seq1.append(delay2)

			seq1.append(pimxPulseQ)   #Pimx
			seq1.append(delay2)			


			seq1.append(COMP4PulseQ)   #Pi2y, Pi2x
			seq1.append(delay2)


			seq1.append(pixPulseQ)  #Pix
			seq1.append(delay2)

			seq1.append(pimyPulseQ)   #Pimy
			seq1.append(delay2)





		self.fungen.create_arbseq('twoPulseI', seq, 1)
		self.fungen.create_arbseq('twoPulseQ',seq1,2)

		self.fungen.wait()
		self.fungen.voltage[1] = 0.500*0.5
		self.fungen.offset[1] = 2*milivolt
		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[1]))

		self.fungen.voltage[2] = 0.480*0.5
		self.fungen.offset[2] = -1*milivolt

		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[2]))

# Sync the two channels 

		self.fungen.sync()
# AWG Output On
		self.fungen.output[1] = 'ON'
		self.fungen.output[2] = 'ON'


# Set the delay generator for triggering the AWG and scope

		self.delaygen.delay['A']=0
		self.delaygen.delay['B']=10e-9
		self.delaygen.Trigger_Source='Internal'
		self.delaygen.trigger_rate=1/trigperiod

		time.sleep(10)

# Set the Source frequency offset from the cavity by IF frequency 
		self.source.set_CW_Freq(cavityfreq+freq)
		self.source.RF_ON()

		time.sleep(5)

		self.osc.average(naverage)  

# Start collecting data
		# measurementno=0
		# while(measurementno<nmeasurement):
			
		# 	measurementno=measurementno+1		
		measurementno=0

		xdata=[]
		ydata=[]

		xdata1=[]
		ydata1=[]


		while(measurementno<=ndelay):
			
			if(measurementno>0):
						self.osc.delaymode_on()
						self.osc.delay_position(0)
						self.osc.delay_time(1.6e-3*measurementno)  
			time.sleep(5)

			self.fungen.output[1] = 'ON'
			self.fungen.output[2] = 'ON'

			self.osc.setmode('average')

			time.sleep(naverage*trigperiod)

			self.osc.datasource(3)
			x,y=self.osc.curv()
			# x = np.array(x)
			x = [m+1.6e-3*measurementno for m in x ]
			# y = np.array(y)
			xdata=xdata+x
			ydata=ydata+y

			self.osc.datasource(4)
			x,y=self.osc.curv()
			# x = np.array(x)
			x = [m+1.6e-3*measurementno for m in x ]
			# y = np.array(y)
			xdata1=xdata1+x
			ydata1=ydata1+y
			time.sleep(5)   # Sleeptime for saving data

			self.fungen.output[1] = 'OFF'
			self.fungen.output[2] = 'OFF'

			self.osc.setmode('sample')
			time.sleep(2)
			measurementno=measurementno+1		

		xdata=np.array(xdata)
		xdata1=np.array(xdata1)
		ydata=np.array(ydata)
		ydata1=np.array(ydata1)

		np.savetxt('D:/MW data/20200811/DROID60/Scan2/ch3/{}_{}.txt'.format(tau*1e6,npulses), np.c_[xdata,ydata])   
		np.savetxt('D:/MW data/20200811/DROID60/Scan2/ch4/{}_{}.txt'.format(tau*1e6,npulses), np.c_[xdata1,ydata1])
		time.sleep(10)   # Sleeptime for saving data

		self.osc.delaymode_off()
		self.source.RF_OFF()


	@Task()
	def Record_DROID60(self):
		params = self.pulse_parameters.widget.get()
		npulses=params['nPulses'].magnitude

		self.osc.delaymode_off()
		self.osc.data_start(1)
		self.osc.data_stop(2000000)  # max resolution ius 4e6, the resolution for 200 ns scale is 5e5
		self.osc.setmode('sample')
		self.source.RF_OFF()
		self.source.Mod_OFF()
		self.source.set_RF_Power(-3) 

		# tau1=params['tau1'].magnitude
		# taustep=params['taustep'].magnitude
		# npoints=params['nPoints'].magnitude

		# for tau in np.linspace(tau1,tau1+(npoints)*taustep,npoints,endpoint=False):
		# 	self.record(tau)
		# return

		tauarray=[6e-6,7e-6,8e-6,9e-6,10e-6,11e-6,12e-6,13e-6,14e-6,15e-6,16e-6,17e-6]

		minreadpulses=8			# Minimum number of pulses that have to be read for having enough datapoints
		oscscale=200e-6         # These two values were chose since I was measuring at 100 MHz so with these settings the sampling resolution is 0.8 ns which is ~ 12 sample per waveform
        						 # This is an optimum choice between keeping the timescale same for all measurements and having enough samples to detect  100 MHz
		maxscale=1e-3            # Based on resolution of 100 MHz with 2M points
								# With this I can read 7 echoes with 0.5 ms
		ndelay=0
		timescale=oscscale
		sc1=3.0e-6

		for tau in tauarray:

			if(tau>=sc1):
				ndelay=round(tau/3.0e-6)
		
				print(ndelay)
			self.osc.time_scale(oscscale)
			self.record(tau,ndelay)



		return

	@Record_DROID60.initializer
	def initialize(self):
		return

	@Record_DROID60.finalizer
	def finalize(self):
		return

	@Element(name='Pulse parameters')
	# Remove the 'config' file from this location everytime you modify the widget:  'C:\Users\zhong\AppData\Roaming\Spyre\main'
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('dc repeat unit', {'type': float, 'default': 50e-9, 'units':'s'}),
		('trigger delay', {'type': float, 'default': 32e-9, 'units':'s'}),	
		('timestep', {'type': float, 'default': 1e-9, 'units':'s'}),
		('period', {'type': float, 'default': 2, 'units':'s'}),
		# ('tau1', {'type': float, 'default': 500e-9, 'units':'s'}),
		# ('taustep', {'type': float, 'default': 50e-6, 'units':'s'}),
		# ('nPoints', {'type': int, 'default': 10, 'units':'dimensionless'}),
		('nPulses', {'type': int, 'default': 5, 'units':'dimensionless'}),
		('nAverage', {'type': int, 'default': 200, 'units':'dimensionless'}),
		# ('nMeasurement', {'type': int, 'default': 1, 'units':'dimensionless'}),
		('IQFrequency', {'type': float, 'default': 1e8, 'units':'dimensionless'}),
		('Phase', {'type': float, 'default': 0, 'units':'dimensionless'}),
		('pulse width', {'type': float, 'default':200e-9, 'units':'s'}),
		('CavityFreq', {'type': float, 'default': 4.9849e9, 'units':'dimensionless'}),
		('Pi2factor', {'type': float, 'default': 0.06, 'units':'dimensionless'}),
		]
		
		w = ParamWidget(params)
		return w
