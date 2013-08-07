import uuid
import datetime
from common_pralka.states import WashingMachineStates

from pralka_server import app, db

class StateRecord(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(80))
    timestamp = db.Column(db.DateTime(timezone=True))
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    payload = db.Column(db.String(300))
    
    def __init__(self, state, device, payload='', timestamp=None):
        self.state = state
        self.device = device
        self.payload = payload
        if timestamp is None:
            timestamp = datetime.datetime.utcnow()
        self.timestamp = timestamp
        super(self, StateRecord).__init__()

    def __repr__(self):
        return '<StateRecord %s device_id=%s>' % (self.state, self.device.id)

class StateChange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(80))
    timestamp = db.Column(db.DateTime(timezone=True))
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    record_id = db.Column(db.Integer, db.ForeignKey('state_record.id'))
    record = db.relationship("StateRecord", backref=db.backref("state_change"))
    
    
    def __init__(self, state, device, causing_record, timestamp=None):
        self.state = state
        self.device = device
        if timestamp is None:
            timestamp = datetime.datetime.utcnow()
        self.timestamp = timestamp
        self.payload = payload
        self.causing_record = causing_record
        super(self, StateChange).__init__()

    def __repr__(self):
        return '<StateChange new_state=%s device_id=%s time=%s>' % \
            (self.state, self.device.id, self.timestamp)
    
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    token = db.Column(db.String(100))
    records = db.relationship("StateRecord", backref=db.backref("device"))
    states = db.relationship("StateChange", backref=db.backref("device"))
    def __init__(self, name):
        self.name = name
        super(Device, self).__init__()

    def set_token(self):
        if self.token is None:
            self.token = uuid.uuid4()

    def def_current_state(self):
        pass
    def add_state_record(self, state, timestamp, payload=''):
        if state not in WashingMachineStates.values:
            raise Exception("State %s is not excepted for a pralka")
        if len(payload) > 300:
            payload = payload[:300]

        state_record = StateRecord(state, self, payload=payload,
            timestamp=timestamp)
        return state_record
