from fastapi.testclient import TestClient
from main import app, active_connections
from database import engine, Base, SessionLocal
import pytest
import json  
from websockets import connect

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    active_connections.clear()
    yield

def test_create_user():
    response = client.post(
        "/users/",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    assert response.json() == {"username": "testuser"}

def test_login():
    client.post("/users/", json={"username": "testuser", "password": "testpass"})
    response = client.post(
        "/token",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_get_messages_empty():
    response = client.get("/messages/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_websocket_chat():
    client.post("/users/", json={"username": "testuser", "password": "testpass"})
    token_response = client.post(
        "/token",
        json={"username": "testuser", "password": "testpass"}
    )
    token = token_response.json()["access_token"]
    async with connect(f"ws://127.0.0.1:8000/chat?token={token}") as ws:
        await ws.send(json.dumps({"content": "Hello"})) 
        response = await ws.recv()
        assert "Hello" in response