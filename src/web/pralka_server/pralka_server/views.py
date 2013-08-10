import datetime

from common_pralka.states import WashingMachineStates
from pralka_server import app, db
from flask import request, session, redirect, url_for, abort, render_template,\
    jsonify
from pralka_server.models import Device, StateRecord
from pralka_server.utils import get_or_404, local_now
from pralka_server import config
import tweepy

@app.route("/")
def hello():
    first = Device.query.order_by('id').first()
    templ_args = dict(has_device=True, device_name='', state=None, state_change=None)
    if first is None:
        templ_args['has_device'] = False
    else:
        templ_args['device_name'] = first.name
        state = first.last_record()
        if state:
            templ_args['state'] = state.state
            templ_args['state_changed'] = state.timestamp
            text = "Current state of %s is %s. Last change: %s" %\
                    (first.name, state.state, state.timestamp)
        
    return render_template('home.html', **templ_args)

@app.route("/contact/")
def contact():
    return render_template('contact.html')

@app.route("/links/")
def links():
    return render_template('links.html')

@app.route("/about/")
def abour():
    return render_template('about.html')

@app.route('/<regex("\d+"):device_id>/device_updates/')
def device_updates():
    pass

@app.route('/twitter_start/<regex("\d+"):device_id>/')
def twitter_start(device_id):
    callback_url = 'http://%s/twitter_complete/%s/' % (config.DOMAIN_NAME, device_id)
    auth = tweepy.OAuthHandler(config.TWITTER_CONSUMER_KEY,
                               config.TWITTER_CONSUMER_SECRET,
                               callback_url)
    authorization_url = auth.get_authorization_url()
    session['request_token'] = (auth.request_token.key, auth.request_token.secret)
    return redirect(authorization_url)

@app.route('/twitter_complete/<regex("\d+"):device_id>/')
def twitter_complete(device_id):
    verifier = request.args.get('oauth_verifier')
    
    auth = tweepy.OAuthHandler(config.TWITTER_CONSUMER_KEY,
                               config.TWITTER_CONSUMER_SECRET)
    request_token = session.get('request_token')
    auth.set_request_token(request_token[0], request_token[1])
    try:
        auth.get_access_token(verifier)
    except tweepy.TweepError, e:
        return str(e)
    
    device = Device.query.filter_by(id=device_id).first()
    if device:
        device.twitter_token = auth.access_token.key
        device.twitter_secret = auth.access_token.secret
        db.session.add(device)
        db.session.commit()
        return 'OK'
    return 'DEVICE NOT FOUND'

@app.route('/api/device/<regex("\d+"):device_id>/update_state/')
def update_api_call(device_id):
    device = get_or_404(Device, device_id)
    token = request.args.get('token')
    if token is None:
        abort(403)

    if token not in [device.token, config.SECRET]:
        abort(403)

    state = request.args.get("state")
    diods = request.args.get("diods", "")
    now = local_now()

    state_record = device.add_state_record(state, now, payload=diods)
    if state_record:
        state_changed = device.got_state_change(state_record)
        if state_changed:
            state_record.state_change = True
            device.state_change_actions(device.last_record(), state_record)

        db.session.add(state_record)
        db.session.commit()
        response = {"state_changed": state_changed, "new_state": state_record.id}
    else:
        response = {"state_changed": False}
    return jsonify(response)


@app.route('/api/device/create/')
def device_create():
    token = request.args.get('token')
    if token != config.SECRET:
        abort(403)
    name = request.args.get('name', 'name1')
    device = Device(name=name)
    db.session.add(device)
    db.session.commit()
    return "OK"

