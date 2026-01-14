from locust import HttpUser, task, between
import random
from datetime import datetime
import json

class FirehoseUser(HttpUser):
    # No wait time between tasks to max out throughput
    wait_time = between(0, 0)

    @task
    def post_event(self):
        payload = {
            "user_id": random.randint(1, 1000000),
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "source": "mobile",
                "version": "1.0.0",
                "action": "click",
                "details": {
                    "x": random.randint(0, 1000),
                    "y": random.randint(0, 1000)
                }
            }
        }
        self.client.post("/event", json=payload)
