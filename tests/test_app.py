import sys
import os
from uuid import uuid4

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from app import app, db, User


def test_home():
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200


def test_get_members():
    with app.test_client() as client:
        response = client.get('/members')
        assert response.status_code == 200


def test_add_member():
    with app.test_client() as client:
        new_member = {
            "name": f"Rohan-{uuid4().hex[:8]}",
            "plan": "Gold"
        }

        response = client.post(
            '/members',
            data=json.dumps(new_member),
            content_type='application/json'
        )

        assert response.status_code == 201
        assert response.json["name"] == new_member["name"]


def test_health():
    with app.test_client() as client:
        response = client.get('/health')
        assert response.json["status"] == "running"


def test_user_registration_and_dashboard():
    username = f"user_{uuid4().hex[:8]}"

    with app.test_client() as client:
        register_response = client.post(
            '/register',
            data={"username": username, "password": "pass123", "role": "user"},
            follow_redirects=True,
        )
        assert register_response.status_code == 200

        login_response = client.post(
            '/login',
            data={"username": username, "password": "pass123"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200
        assert b"This is your user dashboard." in login_response.data


def test_admin_can_create_trainer_and_assign_user():
    trainer_username = f"trainer_{uuid4().hex[:8]}"
    user_username = f"member_{uuid4().hex[:8]}"

    with app.test_client() as client:
        client.post(
            '/register',
            data={"username": user_username, "password": "pass123", "role": "user"},
            follow_redirects=True,
        )

        admin_login = client.post(
            '/login',
            data={"username": "admin", "password": "admin123"},
            follow_redirects=True,
        )
        assert admin_login.status_code == 200
        assert b"Admin Dashboard" in admin_login.data

        create_trainer_response = client.post(
            '/admin/trainers',
            data={
                "username": trainer_username,
                "password": "trainer123",
                "name": "Coach One",
                "specialization": "Strength",
            },
            follow_redirects=True,
        )
        assert create_trainer_response.status_code == 200

        with app.app_context():
            user = User.query.filter_by(username=user_username).first()
            trainer_user = User.query.filter_by(username=trainer_username).first()

        assign_response = client.post(
            '/admin/assign-trainer',
            data={"user_id": user.id, "trainer_id": trainer_user.id},
            follow_redirects=True,
        )
        assert assign_response.status_code == 200
        assert user_username.encode() in assign_response.data
        assert trainer_username.encode() in assign_response.data


def test_trainer_sees_assigned_users():
    trainer_username = f"coach_{uuid4().hex[:8]}"
    user_username = f"client_{uuid4().hex[:8]}"

    with app.test_client() as client:
        client.post(
            '/register',
            data={"username": user_username, "password": "pass123", "role": "user"},
            follow_redirects=True,
        )
        client.post(
            '/login',
            data={"username": "admin", "password": "admin123"},
            follow_redirects=True,
        )
        client.post(
            '/admin/trainers',
            data={
                "username": trainer_username,
                "password": "trainer123",
                "name": "Coach Two",
                "specialization": "Cardio",
            },
            follow_redirects=True,
        )

        with app.app_context():
            user = User.query.filter_by(username=user_username).first()
            trainer_user = User.query.filter_by(username=trainer_username).first()

        client.post(
            '/admin/assign-trainer',
            data={"user_id": user.id, "trainer_id": trainer_user.id},
            follow_redirects=True,
        )

        client.get('/logout', follow_redirects=True)

        trainer_login = client.post(
            '/login',
            data={"username": trainer_username, "password": "trainer123"},
            follow_redirects=True,
        )
        assert trainer_login.status_code == 200
        assert b"Trainer Dashboard" in trainer_login.data
        assert user_username.encode() in trainer_login.data