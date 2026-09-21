"""Flask application factory. Routes only delegate validation/business work to services."""
from flask import Flask, jsonify
from backend.config import Settings
from backend.database import TrafficRepository
from backend.mqtt_client import MqttGateway
from backend.routes.api import api
from backend.services.control_service import ControlService
from backend.services.traffic_service import TrafficService

def create_app(settings: Settings | None = None) -> Flask:
    config=settings or Settings(); app=Flask(__name__)
    repository=TrafficRepository(config.database_path); repository.initialize()
    traffic=TrafficService(repository); mqtt=MqttGateway(config); mqtt.register_handler(traffic.receive_mqtt)
    app.extensions.update(traffic_service=traffic,control_service=ControlService(repository,mqtt),mqtt_gateway=mqtt)
    app.register_blueprint(api)
    @app.errorhandler(ValueError)
    def validation_error(error): return jsonify({"error":str(error)}),400
    @app.get("/health")
    def health(): return {"status":"ok"}
    mqtt.start()
    return app

if __name__ == "__main__": create_app().run(host="0.0.0.0",port=5000,debug=False)
