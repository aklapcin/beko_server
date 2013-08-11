import time
import subprocess
import math
from common_pralka.states import WashingMachineStates, DiodsStates
class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        return super(Point, self).__init__()

    def moved_by(self, vector):
        return Point(self.x + vector[0], self.y + vector[1])
    
    def distance(self, other):
        xd_sq = (self.x - other.x)* (self.x - other.x)
        yd_sq = (self.y - other.y)* (self.y - other.y)
        return math.sqrt(float(xd_sq + yd_sq))

class DiodState(object):
    STATES = DiodsStates

    def __init__(self, center, state):
        self.center = Point(center[0], center[1])
        self.state = state

    def in_range(self, range_center, r):
        return self.center.distance(range_center) <= r

    def is_on(self):
        return self.state == self.STATES.ON

class MachineState(object):
    STATES = WashingMachineStates
    STATES_DIODS = {
        STATES.ON: [True, False, False, False, False],
        STATES.FINISHED: [True, False, False, False, True],
        STATES.WASHING: [True, True, False, False, False],
        STATES.RINSING: [False, False, True, False, False],
        STATES.SPINING: [False, False, False, True, False]}

    DIODS_DISTANCE = Point(22, 210)

    def __init__(self, diods_state, filename, calculate=False):
        self.diods_state = []
        for d in diods_state:
            print d
            self.diods_state.append(DiodState(d[0], d[1] and DiodState.STATES.ON or DiodState.STATES.OFF))
        self.state = self.STATES.UNKNOWN
        self.filename = filename
        if calculate:
            self.calculate_state()

    def calculate_state(self):
        if len(self.diods_state) == 0:
            self.state = self.STATES.OFF
            return
        if len(self.diods_state) < 4:
            self.state = self.STATES.UNKNOWN
            return
        if not self.check_diods_ok():
            self.state = self.STATES.UNKNOWN
            return
        print self.diods_on_state
        for state_name, diods_on in self.STATES_DIODS.items():
            if self.diods_on_state == diods_on: 
                self.state = state_name
                break
        
    @property
    def diods_on_state(self):
        return [x.is_on() for x in self.diods_state]
    

    def check_diods_ok(self):
        i = 0
        while True:
            if i + 1 >= len(self.diods_state):
                break

            c_diod = self.diods_state[i]
            next_diod = self.diods_state[i + 1]
            
            next_diod_should_be = c_diod.center.moved_by([self.DIODS_DISTANCE.x, self.DIODS_DISTANCE.y])
            if next_diod.in_range(next_diod_should_be, 30):
                i += 1
                continue  # everything ok, checking next diod

            next_next_diod_should_be = c_diod.center.moved_by([self.DIODS_DISTANCE.x * 2, self.DIODS_DISTANCE.y * 2])
            if next_diod.in_range(next_next_diod_should_be, 30):
                missed_diod = DiodState((c_diod.center.x+ self.DIODS_DISTANCE.x, c_diod.center.y + self.DIODS_DISTANCE.y), 'UNKNOWN')
                self.diods_state.insert(i+1, missed_diod)
                print "inserting missing diod at %s, %s"% (missed_diod.center.x, missed_diod.center.y)
                i += 1
                continue  # everything ok, checking next diod
            # next diod is not in line. remove ir
            print "removing bad diod i=%s current diod is at %s %s, next is at %s %s" %\
                    (i, c_diod.center.x, c_diod.center.y, next_diod.center.x, next_diod.center.y)
                
            self.diods_state.pop(i+1)
            i += 1
        
        if len(self.diods_state) == 5:
            return True
        
        return False

    def record(self):
        message = '\n'.join([self.filename, self.state, ','.join([x.state for x in self.diods_state])]) + '\n'
        return message
        
