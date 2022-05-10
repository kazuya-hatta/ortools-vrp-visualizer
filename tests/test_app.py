import pytest
from starlette.testclient import TestClient
from ortools_viz_backend.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_index(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
