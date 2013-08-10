from enum import EnumMetaclass

class WashingMachineStates(object):
    __metaclass__ = EnumMetaclass
    OFF = 'off'
    ON = 'on'
    FINISHED = 'finished'
    WASHING = 'washing'
    RINSING = 'rinsing'
    SPINING = 'spining'
    UNKNOWN = 'unknown'

class DiodsStates(object):
    __metaclass__ = EnumMetaclass
    OFF = 'off'
    ON = 'on'
    UNKNOWN = 'unknown'
    