from common_pralka.states import WashingMachineStates
from pralka_server import app, db
from flask import request
from pralka_server.models import Device, StateChange, StateRecord
from pralka_server.utils import get_or_404

@app.route("/")
def hello():

    text = "Current state of "
    return 

@app.route('/<regex("\d+"):device_id>/device_updates/')
def device_updates():
    pass

@app.route('/<regex("\d+"):device_id>/device_states/')
def device_states():
    pass

@app.route('/api/<regex("\d+"):device_id>/update_state')
def update_api_call(device_id):
    device = get_or_404(Device, device_id)
    token = request.args.get('token')
    if token is None:
        abort(403)

    if device.token != token:
        abort(403)

    state = request.args.get("state")
    diods = request.args.get("diods", "")
    now = datetime.datetime.utcnow()

    state_record = device.add_state_record(state, now, payload="diods")
    updated_state = device.update_state()
    if updated_state is not None:
        db.session.add(updated_state)
    db.session.add(state_record)
    db.session.commit()

