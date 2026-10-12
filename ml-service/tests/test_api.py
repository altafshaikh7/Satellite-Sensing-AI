import numpy as np
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_validate_single_file(write_raster):
    path = write_raster("s2.tif", np.full((13, 64, 64), 500, dtype="uint16"))
    r = client.post("/validate", json={"files": [{"path": path, "modality": "optical"}]})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_validate_missing_file_reports_error():
    r = client.post("/validate", json={"files": [{"path": "does_not_exist.tif"}]})
    assert r.json()["ok"] is False