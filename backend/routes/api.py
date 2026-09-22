from flask import Blueprint, current_app, jsonify, request

api = Blueprint("api", __name__, url_prefix="/api")
def traffic_service(): return current_app.extensions["traffic_service"]
def control_service(): return current_app.extensions["control_service"]

def body():
    value=request.get_json(silent=True)
    if not isinstance(value,dict): raise ValueError("JSON object body required")
    return value

@api.get("/status")
def status(): return jsonify(traffic_service().status())
@api.get("/traffic")
def traffic(): return jsonify({"traffic": traffic_service().repository.history(int(request.args.get("limit",50)))})
@api.get("/signals")
def signals(): return jsonify(traffic_service().repository.latest_signal_payloads())
@api.get("/history")
def history(): return jsonify({"traffic":traffic_service().repository.history(int(request.args.get("limit",50)))})
@api.get("/events")
def events(): return jsonify({"events":traffic_service().repository.events(int(request.args.get("limit",50)))})
@api.post("/traffic")
def receive_ai(): traffic_service().receive_ai(body()); return jsonify({"accepted":True}),201
@api.post("/control")
def control(): return jsonify(control_service().control(body())),202
@api.post("/manual")
def manual(): return jsonify(control_service().manual(body())),202
@api.post("/emergency")
def emergency(): return jsonify(control_service().emergency(body())),202
