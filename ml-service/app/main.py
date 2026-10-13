import time
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import OUTPUTS_DIR
from controller import router
from controller.executor import run_plan
from controller.integrator import build
from tracing.logger import save_trace
from tracing.report import write_report
from validator import aligner, band_check, geo_checker

# Sentinel-2 4-band stack written by scripts/stack_s2_bands.py: B02, B03, B04, B08
DEFAULT_BAND_MAP = {"blue": 0, "green": 1, "red": 2, "nir": 3}

app = FastAPI(title="SatQuery ML service")


class FileIn(BaseModel):
    path: str
    modality: str | None = None  # "optical" or "sar"


class ValidateRequest(BaseModel):
    files: list[FileIn] = Field(min_length=1, max_length=2)


class AnalyzeRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    files: list[FileIn] = Field(min_length=1, max_length=2)
    band_map: dict[str, int] = Field(default_factory=lambda: dict(DEFAULT_BAND_MAP))
    boa_offset: float = -1000.0
    sar_vv_index: int = 0
    tool_params: dict[str, dict] = Field(default_factory=dict)


@app.get("/health")
def health():
    return {"status": "ok"}


def _validate(files: list[FileIn]) -> dict:
    file_checks = [band_check.check_file(f.path, f.modality) for f in files]
    pair = None
    if len(files) == 2 and all(c["ok"] for c in file_checks):
        pair = geo_checker.check_pair(files[0].path, files[1].path)
    ok = all(c["ok"] for c in file_checks) and (pair is None or pair["ok"])
    return {"ok": ok, "files": file_checks, "pair": pair}


@app.post("/validate")
def validate(req: ValidateRequest):
    return _validate(req.files)


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    t0 = time.time()
    checks = _validate(req.files)
    if not checks["ok"]:
        raise HTTPException(status_code=422, detail=checks)

    modalities = [c["modality"] for c in checks["files"]]
    try:
        config = router.input_config(modalities)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Optical first for optical+SAR (reference grid), otherwise upload order.
    order = list(range(len(req.files)))
    if config == "optical_sar":
        order.sort(key=lambda i: modalities[i] != "optical")

    run_id = uuid.uuid4().hex
    paths = [req.files[i].path for i in order]
    items = [{"path": paths[k], "modality": checks["files"][i]["modality"],
              "sar_scale": checks["files"][i]["sar_scale"]} for k, i in enumerate(order)]

    alignment = None
    if len(paths) == 2:
        pair_now = geo_checker.check_pair(paths[0], paths[1])
        if not pair_now["same_grid"]:
            out = OUTPUTS_DIR / "aligned" / f"{run_id}_second.tif"
            aligner.align_to_reference(paths[0], paths[1], str(out))
            alignment = {
                "applied": True,
                "method": "bilinear reprojection to reference grid",
                "reference": paths[0],
                "source": paths[1],
                "output": str(out),
                "reasons": pair_now["warnings"],
            }
            paths[1] = str(out)
            items[1]["path"] = paths[1]

    optical = next((it for it in items if it["modality"] == "optical"), None)
    sar = next((it for it in items if it["modality"] == "sar"), None)

    ctx = {
        "query": req.query,
        "band_map": req.band_map,
        "boa_offset": req.boa_offset,
        "sar_vv_index": req.sar_vv_index,
        "before": paths[0],
        "after": paths[1] if len(paths) == 2 else None,
        "optical": optical["path"] if optical else None,
        "sar": sar["path"] if sar else None,
        "sar_scale": sar["sar_scale"] if sar else None,
        "ref": paths[0],
    }

    plan = router.route(config, req.query)
    results, tool_log = run_plan(plan, ctx, req.tool_params)
    answer, evidence, confidence, limitations = build(results, ctx, run_id)

    trace = {
        "run_id": run_id,
        "ts": time.time(),
        "query": req.query,
        "input_config": config,
        "modalities": modalities,
        "parameters": {"band_map": req.band_map, "boa_offset": req.boa_offset,
                       "sar_vv_index": req.sar_vv_index},
        "input_checks": {"files": checks["files"], "pair": checks["pair"]},
        "alignment": alignment,
        "plan": plan,
        "tools": tool_log,
        "answer": answer,
        "evidence": evidence,
        "confidence": confidence,
        "limitations": limitations,
        "total_ms": round((time.time() - t0) * 1000),
    }
    save_trace(trace)
    write_report(trace)
    return {**trace, "report_url": f"/outputs/reports/{run_id}.html"}