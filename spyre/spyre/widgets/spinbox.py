from pyqtgraph import SpinBox as _SpinBox
from lantz import Q_
from pint.util import infer_base_unit

class SpinBox(_SpinBox):

    def __init__(self, parent=None, value=1.0, unit=None, **kwargs):
        self.unit = unit
        self.base_unit = None
        kwargs['dec'] = kwargs.pop('dec', True)
        kwargs['minStep'] = kwargs.pop('minStep', 0.1)
        kwargs['decimals'] = kwargs.pop('decimals', 8)
        kwargs['compactHeight'] = False
        if self.unit is not None:
            q = Q_(unit)
            base_units = infer_base_unit(q)
            base_unit = '*'.join('{} ** {}'.format(u, p) for u, p in base_units.items())
            base_unit = base_unit if not base_unit == '' else 'dimensionless'
            q_base = Q_(base_unit)
            factor = (q / q_base).to_base_units().m
            self.base_unit = base_unit
            opts = {
                'suffix': '{0.units:~}'.format(q_base),
                'siPrefix': True,
            }
            kwargs.update(opts)
            value *= factor
        super().__init__(parent=parent, value=value, **kwargs)
        return

    def unit_value(self):
        val = super().value()
        uval = Q_(val, self.base_unit) if self.base_unit is not None else val
        return uval

    def setValue(self, value=None, **kwargs):
        if type(value) is Q_:
            value = value.to_base_units().m
        # print(value)
        super().setValue(value=value, **kwargs)
