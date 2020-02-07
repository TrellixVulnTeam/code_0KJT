import numpy as np
import pyqtgraph as pg
import time

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time

from lantz.drivers.anritsu import MS2721B
from lantz.log import log_to_screen, DEBUG

class SpectrumAnalyzer(Spyrelet):
    
    requires = {
        'spa': MS2721B
    }

    @Task()
    def set(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        freq_params = self.Frequency_Settings.widget.get()
        # amp_params = self.Frequency_Settings.widget.get()
        span = freq_params['frequency span']
        center = freq_params['center freq']
        # ref = amp_params['ref level']
        self.spa.freq_span = span
        self.spa.freq_cent = center
        # self.spa.ref_level = ref
        #self.spa.freq_star = start
        print('set frequency span to {}'.format(span))
        print('set center frequency to {}'.format(center))
        # print('set reference level to {}'.format(ref))


    @set.initializer
    def initialize(self):
        print('initialize')
        print('idn: {}'.format(self.spa.idn))
        return

    @set.finalizer
    def finalize(self):
        print('finalize')
        return

    @Element()
    def Frequency_Settings(self):
        freq_params = [
        ('frequency span', {'type': float, 'default': 3000, 'units': 'Hz'}),
        ('center freq', {'type': float, 'default': 30000000, 'units': 'Hz'}),
        ]
        w = ParamWidget(freq_params)
        return w

  