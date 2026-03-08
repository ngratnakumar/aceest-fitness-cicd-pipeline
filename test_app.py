import pytest
from app import app

@pytest.fixture
def client():
    return app.test_client()

def test_homepage(client):
    """Test if the dashboard loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"ACEest Fitness Dashboard" in response.data