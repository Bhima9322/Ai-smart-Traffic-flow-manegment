import tempfile
import unittest
from pathlib import Path
from backend.database import TrafficRepository
from backend.mqtt_client import MqttGateway, TOPICS
from backend.config import Settings
from backend.services.control_service import ControlService
from backend.services.traffic_service import TrafficService

class RecordingMqtt(MqttGateway):
    def __init__(self): self.messages=[]
    def publish(self, topic, payload, retain=False): self.messages.append((topic,payload,retain))

class BackendServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.repo=TrafficRepository(Path(self.temp.name)/"test.db"); self.repo.initialize(); self.traffic=TrafficService(self.repo); self.mqtt=RecordingMqtt(); self.control=ControlService(self.repo,self.mqtt,clock=lambda:"2026-01-01T00:00:00Z")
    def tearDown(self): self.temp.cleanup()
    def test_ai_and_mqtt_data_are_stored(self):
        self.traffic.receive_ai({"a":4,"b":15,"timestamp":"2026-01-01T00:00:00Z"})
        self.traffic.receive_mqtt(TOPICS["status_b"],{"state":"GREEN","green_time":45,"timestamp":"2026-01-01T00:00:01Z"})
        self.assertEqual(self.repo.history(),[{"timestamp":"2026-01-01T00:00:00Z","a":4,"b":15}]); self.assertEqual(self.repo.latest_signal_payloads()["B"]["green_time"],45)
    def test_control_publishes_validated_command(self):
        command=self.control.control({"signal":"B","state":"GREEN","green_time":45,"reason":"TIME_TRANSFER"})
        self.assertEqual(command["green_time"],45); self.assertEqual(self.mqtt.messages[0][0],TOPICS["control"])
    def test_emergency_publishes(self):
        self.control.emergency({"direction":"B","active":True,"priority_duration":20})
        self.assertEqual(self.mqtt.messages[0][0],TOPICS["emergency"])
    def test_invalid_control_rejected(self):
        with self.assertRaises(ValueError): self.control.control({"signal":"A","state":"GREEN","green_time":"45"})
