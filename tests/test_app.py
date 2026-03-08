import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from app import app

client = app.test_client()


def test_home():
    response = client.get('/')
    assert response.status_code == 200


def test_get_members():
    response = client.get('/members')
    assert response.status_code == 200


def test_add_member():
    new_member = {
        "id": 3,
        "name": "Rohan",
        "plan": "Gold"
    }

    response = client.post(
        '/members',
        data=json.dumps(new_member),
        content_type='application/json'
    )

    assert response.status_code == 201


def test_health():
    response = client.get('/health')
    assert response.json["status"] == "running"