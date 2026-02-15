"""
Quick test script for the microservice that uses FastAPI TestClient.

Run after installing requirements (see README):
python run_test.py
"""
from fastapi.testclient import TestClient
from app import app


def test_trending():
    client = TestClient(app)
    r = client.get("/trending?limit=3")
    print("status:", r.status_code)
    print(r.json())


if __name__ == "__main__":
    test_trending()
