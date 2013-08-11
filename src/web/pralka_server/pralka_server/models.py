import time
import random
import uuid
import datetime
import tweepy

from common_pralka.states import WashingMachineStates

from pralka_server import app, db, config

class StateRecord(db.Model):
    ALLOWED_TRANSITIONS = {
        WashingMachineStates.OFF: [WashingMachineStates.ON, WashingMachineStates.WASHING],
        WashingMachineStates.ON: [WashingMachineStates.WASHING],
        WashingMachineStates.WASHING: [WashingMachineStates.RINSING, WashingMachineStates.SPINING],
        WashingMachineStates.RINSING: [WashingMachineStates.SPINING, WashingMachineStates.FINISHED, WashingMachineStates.OFF],
        WashingMachineStates.SPINING: [WashingMachineStates.FINISHED, WashingMachineStates.OFF],
        WashingMachineStates.FINISHED: [WashingMachineStates.OFF, WashingMachineStates.ON]
    }


    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(80))
    timestamp = db.Column(db.DateTime(timezone=True))
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    payload = db.Column(db.String(300))
    changes_state = db.Column(db.Boolean, default=False)
    def __init__(self, state, device, payload='', timestamp=None):
        self.state = state
        self.device = device
        self.payload = payload
        if timestamp is None:
            timestamp = datetime.datetime.utcnow()
        self.timestamp = timestamp
        super(StateRecord, self).__init__()

    def __repr__(self):
        return '<StateRecord %s device_id=%s>' % (self.state, self.device.id)

    
class Device(db.Model):
    STATES = WashingMachineStates

    TWEETS = {
        "off_on": ["I am alive.", "Just got turend on. THANK-YOU-OWNER!", "On again!", "Hello world!!!"],
        "off_washing": ["Let's wash some cloths", "Time to start working."],
        "on_washing": ["Now washing time", "I was waiting for it. Washing time!"],
        "washing_rinsing": ["Let's get rid of detergent", "Core washing done. Now getting rid of detergent"],
        "washing_spining": ["Lets get rid of water", "Spiiiiiiining"],
        "rinsing_spining": ["Whiiii... (spinning fast)", "Spiiining time"],
        "rinsing_finished": ["Finished. Fresh load of clean cloths waiting for drying", "Aaaaaaaaaand DONE."],
        "rinsing_off": ["I am off", "I've just got shut down."],
        "spining_finished": ["Finished. Fresh load of clean cloths waiting for drying", "Aaaaaaaaaand DONE."],
        "spining_off": ["I am off", "I've just got shut down."],
        "finished_off": ["I am off", "I've just got shut down."],
        "finished_on": ["On again", "Good Morning! Waiting for next load"],

    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    token = db.Column(db.String(100))
    twitter_token = db.Column(db.String(200))
    twitter_secret = db.Column(db.String(200))
    tweet_on_state_change = db.Column(db.Boolean(), default=True)
    records = db.relationship("StateRecord", backref=db.backref("device"))
    
    def __init__(self, name):
        self.name = name
        self.set_token()
        super(Device, self).__init__()

    def set_token(self):
        if self.token is None:
            randint = random.getrandbits(128)
            self.token = str(uuid.uuid4())

    def last_record(self, before=None):
        records = StateRecord.query.filter_by(device_id=self.id)
        if before is not None:
            records = records.filter(StateRecord.timestamp < before)
        return records.order_by(StateRecord.timestamp.desc()).first()

    def got_state_change(self, new_record):
        
        last_record = self.last_record(before = new_record.timestamp)
        if last_record is None:
            return True
        if last_record.timestamp < new_record.timestamp - datetime.timedelta(0, 60*60):
            # logging.info("last state is too old")
            return False
        if new_record.state in StateRecord.ALLOWED_TRANSITIONS[last_record.state]:
            return True
        return False
    
    def accept_new_state(self, new_record):
        last_record = self.last_record(before = new_record.timestamp)
        if last_record is None:
            return True
        if last_record.timestamp < new_record.timestamp - datetime.timedelta(0, 60*30):
            return True
        if new_record.state in StateRecord.ALLOWED_TRANSITIONS[last_record.state]:
            return True
        if new_record.state == last_record.state:
            return True
        return False
        
    def state_change_actions(self, last_state, new_state):
        if self.tweet_on_state_change:
            self.tweet_state_change(last_state, new_state)

    def tweet_state_change(self, last_state, new_state):
        if self.tweet_on_state_change:
            
            if self.twitter_token is None or self.twitter_secret is None:
                return

            auth = tweepy.OAuthHandler(config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
            auth.set_access_token(self.twitter_token, self.twitter_secret)

            api = tweepy.API(auth_handler=auth)

            state_key = "%s_%s" % (last_state.state, new_state.state)
            print "sending tweet"
            
            tweets = self.TWEETS.get(state_key)
            if tweets is None:
                print "did not found tweets for %s" % state_key
                return
            
            tweet = tweets[random.randint(0, len(tweets)-1)]
            tweet += " #tweetingwashingmachine"
            tweet += " (" + str(int(time.time()))[-7:] + ")"
            try:
                api.update_status(status=tweet)
                print "Tweet %s sent" % tweet
            except Exception, e:
                print "Exception %s" % e

    def add_state_record(self, state, timestamp, payload=''):
        if state not in WashingMachineStates.values:
            raise Exception("State %s is not excepted for a pralka, should be in %s" % \
                                (state, WashingMachineStates.values))
        if len(payload) > 300:
            payload = payload[:300]

        state_record = StateRecord(state, self, payload=payload,\
            timestamp=timestamp)
        if self.accept_new_state(state_record):
            return state_record
        return None
