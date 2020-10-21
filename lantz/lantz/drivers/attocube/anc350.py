from lantz.foreign import LibraryDriver
from lantz import Feat, DictFeat, Action, Q_

import time
from ctypes import c_uint, c_void_p, c_double, pointer, POINTER

# test message
#  test message 2
# test message 3
# test message 4
# test message 5
# test message 6

class ANC350(LibraryDriver):

    LIBRARY_NAME = 'anc350v3.dll'
    LIBRARY_PREFIX = 'ANC_'

    RETURN_STATUS = {0:'ANC_Ok', -1:'ANC_Error', 1:"ANC_Timeout", 2:"ANC_NotConnected", 3:"ANC_DriverError",
                     7:"ANC_DeviceLocked", 8:"ANC_Unknown", 9:"ANC_NoDevice", 10:"ANC_NoAxis",
                     11:"ANC_OutOfRange", 12:"ANC_NotAvailable"}

    def __init__(self):
        super(ANC350, self).__init__()

        #Discover systems
        ifaces = c_uint(0x01) # USB interface
        devices = c_uint()
        self.check_error(self.lib.discover(ifaces, pointer(devices)))
        if not devices.value:
            raise RuntimeError('No controller found. Check if controller is connected or if another application is using the connection')
        self.dev_no = c_uint(devices.value - 1)
        self.device = None

        # Function definitions
        self.lib.getFrequency.argtypes = [c_void_p, c_uint, POINTER(c_double)]
        self.lib.setFrequency.argtypes = [c_void_p, c_uint, c_double]
        self.lib.setDcVoltage.argtypes = [c_void_p, c_uint, c_double]
        self.lib.getPosition.argtypes = [c_void_p, c_uint, POINTER(c_double)]
        self.lib.measureCapacitance.argtypes = [c_void_p, c_uint, POINTER(c_double)]
        self.lib.startContinousMove.argtypes = [c_void_p, c_uint, c_uint, c_uint]
        self.lib.setTargetPosition.argtypes = [c_void_p, c_uint, c_double]
        self.lib.setTargetRange.argtypes = [c_void_p, c_uint, c_double]
        self.lib.disconnect.argtypes = [c_void_p]
        return

    def initialize(self, devNo=None):
        if not devNo is None: self.devNo = devNo
        device = c_void_p()
        self.check_error(self.lib.connect(self.dev_no, pointer(device)))
        self.device = device

        #Wait until we get something else then 0 on the position
        while(self.position[2] == Q_(0, 'um')):time.sleep(0.025)

    def finalize(self):
        self.check_error(self.lib.disconnect(self.device))
        self.device = None

    def check_error(self, err):
        if err != 0:
            raise Exception("Driver Error {}: {}".format(err, self.RETURN_STATUS[err]))
        return

    @DictFeat(units='Hz')
    def frequency(self, axis):
        ret_freq = c_double()
        self.check_error(self.lib.getFrequency(self.device, axis, pointer(ret_freq)))
        return ret_freq.value

    @frequency.setter
    def frequency(self, axis, freq):
        self.check_error(self.lib.setFrequency(self.device, axis, freq))
        return

    @DictFeat(units='V')
    def amplitude(self, axis):
        ret_ampl = c_double()
        self.check_error(self.lib.getAmplitude(self.device, axis, pointer(ret_freq)))
        return ret_ampl.value

    @amplitude.setter
    def amplitude(self, axis, ampl):
        self.check_error(self.lib.setAmplitude(self.device, axis, ampl))
        return


    def DCvoltage(self, axis,vol):
        self.check_error(self.lib.setDcVoltage(self.device, axis, vol))
        return


    @DictFeat(units='um')
    def position(self, axis):
        ret_pos = c_double()
        self.check_error(self.lib.getPosition(self.device, axis, pointer(ret_pos)))
        return ret_pos.value * 1e6

    @position.setter
    def position(self, axis, pos):
        return self.absolute_move(axis, pos)


    @DictFeat(units='F')
    def capacitance(self, axis):
        ret_c = c_double()
        self.check_error(self.lib.measureCapacitance(self.device, axis, pointer(ret_c)))
        return ret_c.value

    @DictFeat()
    def status(self, axis):
        status_names = [
            'connected',
            'enabled',
            'moving',
            'target',
            'eot_fwd',
            'eot_bwd',
            'error',
        ]
        status_flags = [c_uint() for _ in range(7)]
        status_flags_p = [pointer(flag) for flag in status_flags]
        self.check_error(self.lib.getAxisStatus(self.device, axis, *status_flags_p))

        ret = dict()
        for status_name, status_flag in zip(status_names, status_flags):
            ret[status_name] = True if status_flag.value else False
        return ret

    # Untested
    @Action()
    def stop(self):
        for axis in range(3):
            self.lib.startContinousMove(self.device, axis, 0, 1)


    @Action()
    def jog(self, axis, speed):
        backward = 0 if speed >= 0.0 else 1
        start = 1 if speed != 0.0 else 0
        self.check_error(self.lib.startContinousMove(self.device, axis, start, backward))
        return
    @Action()
    def continousmove(self, axis,direction):
        self.lib.startContinousMove(self.device, axis,True,direction)
        return
    @Action()
    def stopmove(self, axis):
        self.lib.startContinousMove(self.device, axis,False,1)
        return



    @Action()
    def single_step(self, axis, direction):
        # if direction<=0 then True
        ## then backward = True
        # if direction is not <=0 then False
        ## then backward = False
        # so pass a number >0 into single step to specify the forward direction
        backward = direction <= 0
        self.lib.startSingleStep(self.device, axis, backward)
        return

    MAX_ABSOLUTE_MOVE = Q_(1000, 'um')
    @Action()
    def absolute_move(self, axis, target, eps=0.1, max_move=MAX_ABSOLUTE_MOVE):
        if not max_move is None:
            if abs(self.position[axis]-Q_(target, 'um')) > max_move:
                raise Exception("Relative move %f-%f um is greater then the %f um"%(self.position[axis].magnitude,Q_(target, 'm').magnitude,max_move.magnitude))
        target = target*1e-6
        eps = eps*1e-6
        self.check_error(self.lib.setTargetRange(self.device, axis, eps))
        self.check_error(self.lib.setTargetPosition(self.device, axis, target))
        enable = 0x01
        relative = 0x00
        self.check_error(self.lib.startAutoMove(self.device, axis, enable, relative))
        return

    MAX_RELATIVE_MOVE = Q_(1000, 'um')
    @Action()
    def relative_move(self, axis, delta):
        delta = Q_(delta, 'um')
        if abs(delta) > MAX_RELATIVE_MOVE:
            raise Exception("Relative move %f is greater then the MAX_RELATIVE_MOVE"%(delta))
        else:
            target = self.position + delta
            target = target.to('m').magnitude
            print(target)
            # self.absolute_move(axis, target)


    @Action()
    def relative_move(self, axis, delta, max_move=MAX_RELATIVE_MOVE):
        target = self.position[axis].magnitude + delta
        #target = target.to('um').magnitude
        print("Moving to {}".format(target))
        self.absolute_move(axis, target, max_move=max_move)

    @Action()
    def set_target_range(self, axis, target_range):
        self.check_error(self.lib.setTargetRange(self.device, axis, target_range))
        return

    @Action()
    def dc_bias(self, axis, voltage):
        self.check_error(self.lib.setDcVoltage(self.device, axis, voltage))
        return

    # ----------------------------------------------
    # Closed-loop Actions
    # These action are much slower but they ensure the move completed
    @Action(units=(None, 'um', 'um', None, 'seconds', None, None))
    def cl_move(self, axis, pos, delta_z=Q_(0.1,'um'), iter_n=4, delay=Q_(0.05, 's'), debug=False, max_iter=1000):
        i = 0
        while(not self.at_pos(axis=axis,pos=Q_(pos, 'um'), delta_z=Q_(delta_z, 'um'), iter_n=iter_n, delay=Q_(delay,'s'))):
            self.position[axis] = Q_(pos, 'um')
            time.sleep(0.2)
            i += 1
            #if i>=max_iter:
            #    raise Exception("Reached max_iter")
        if debug: print("It took {} iterations to move to position".format(i))
        return

    @Action(units=(None, 'um', 'um', None, 'seconds'))
    def at_pos(self, axis, pos, delta_z=Q_(0.2,'um'), iter_n=2, delay=Q_(0.1, 's')):
        for i in range(iter_n):
            time.sleep(delay)
            if abs(self.position[axis].to('um').magnitude-pos)>delta_z:
                return False
        return True
    # ----------------------------------------------

    # Untested
    @Action()
    def stop(self):
        for axis in range(3):
            self.check_error(self.lib.startContinousMove(self.device, axis, 0, 1))
