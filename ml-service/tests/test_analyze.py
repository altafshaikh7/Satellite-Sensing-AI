import numpy as np
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _bitemporal_pair(write_raster):
    rng = np.random.default_rng(0)
    before = np.zeros((4, 64, 64), dtype="uint16")
    before[0] = 2000 + rng.integers(0, 40, (64, 64))
    before[1] = 2000 + rng.integers(0, 40, (64, 64))
    before[2] = 1200 + rng.integers(0, 40, (64, 64))   # red
    before[3] = 4000 + rng.integers(0, 40, (64, 64))   # nir, vegetation

    after = before.copy()
    after[2, 10:26, 10:26] = 3000   # red up
    after[3, 10:26, 10:26] = 1500   # nir down: vegetation loss block
    return write_raster("before.tif", before), write_raster("after.tif", after)


def test_bitemporal_change_runs_and_writes_mask(write_raster):
    before, after = _bitemporal_pair(write_raster)
    body = {
        "query": "Where did it change?",
        "files": [{"path": before, "modality": "optical"}, {"path": after, "modality": "optical"}],
    }
    r = client.post("/analyze", json=body)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["plan"] == ["change"]
    assert data["tools"][0]["status"] == "ok"
    assert data["evidence"]["stats"]["change_changed_pct"] > 0
    assert data["evidence"]["masks"][0]["url"].startswith("/outputs/masks/")
    assert data["report_url"].startswith("/outputs/reports/")


def test_vlm_tool_reports_unavailable_without_weights(write_raster, monkeypatch, tmp_path):
    monkeypatch.setenv("VLM_PATH", str(tmp_path / "missing_weights"))
    data = np.full((4, 64, 64), 1500, dtype="uint16")
    path = write_raster("single.tif", data)
    body = {"query": "Describe the land cover", "files": [{"path": path, "modality": "optical"}]}
    r = client.post("/analyze", json=body)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["plan"] == ["vqa"]
    assert out["tools"][0]["status"] == "unavailable"
    assert "weights not found" in out["answer"]


def test_rejected_param_is_logged_not_run(write_raster, monkeypatch, tmp_path):
    monkeypatch.setenv("VLM_PATH", str(tmp_path / "missing_weights"))
    before, after = _bitemporal_pair(write_raster)
    body = {
        "query": "Where did it change?",
        "files": [{"path": before, "modality": "optical"}, {"path": after, "modality": "optical"}],
        "tool_params": {"change": {"min_area_px": 0}},
    }
    r = client.post("/analyze", json=body)
    assert r.status_code == 200, r.text
    assert r.json()["tools"][0]["status"] == "rejected"