from fastapi.testclient import TestClient
from main import app
from app.core.config import get_settings

settings = get_settings()
client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "hello neps",
        "app_name": settings.APP_NAME,
        "app_env": settings.APP_ENV,
        "redcap_mock_enabled": settings.REDCAP_MOCK_ENABLED
    }