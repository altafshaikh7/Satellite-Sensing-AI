from fastapi import FastAPI
from pydantic import BaseModel, Field

from validator import band_check, geo_checker

app = FastAPI(title="SatQuery ML service")


class FileIn(BaseModel):
    path: str
    modality: str | None = None  # "optical" or "sar"


class ValidateRequest(BaseModel):
    files: list[FileIn] = Field(min_length=1, max_length=2)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/validate")
def validate(req: ValidateRequest):
    files = [band_check.check_file(f.path, f.modality) for f in req.files]
    pair = None
    if len(req.files) == 2 and all(f["ok"] for f in files):
        pair = geo_checker.check_pair(req.files[0].path, req.files[1].path)
    ok = all(f["ok"] for f in files) and (pair is None or pair["ok"])
    return {"ok": ok, "files": files, "pair": pair}