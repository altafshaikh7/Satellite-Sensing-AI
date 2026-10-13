import { Router } from "express";
import path from "path";
import { upload } from "./upload.js";
import { mlGet, mlPost } from "./mlClient.js";

const router = Router();

function httpError(msg, status = 400) {
  const e = new Error(msg);
  e.status = status;
  return e;
}

function parseJSON(value, fallback) {
  if (value === undefined || value === "") return fallback;
  try {
    return JSON.parse(value);
  } catch {
    throw httpError(`invalid JSON in form field: ${value}`);
  }
}

function parseList(value) {
  if (!value) return [];
  const s = String(value).trim();
  if (s.startsWith("[")) {
    try { return JSON.parse(s); } catch { /* fall through */ }
  }
  return s.replace(/[\[\]"']/g, "").split(",").map((x) => x.trim()).filter(Boolean);
}
function filesFromRequest(req) {
  if (!req.files || req.files.length === 0) {
    throw httpError("upload 1 or 2 GeoTIFF files in the form field 'images'");
  }
  const modalities = parseList(req.body.modalities);
  return req.files.map((f, i) => ({
    path: path.resolve(f.path),
    modality: modalities[i] || null,
  }));
}

router.get("/health", async (req, res, next) => {
  try {
    res.json({ gateway: "ok", ml: await mlGet("/health") });
  } catch (e) {
    next(e);
  }
});

router.post("/validate", upload, async (req, res, next) => {
  try {
    const files = filesFromRequest(req);
    res.json(await mlPost("/validate", { files }));
  } catch (e) {
    next(e);
  }
});

router.post("/query", upload, async (req, res, next) => {
  try {
    const files = filesFromRequest(req);
    if (!req.body.query) throw httpError("form field 'query' is required");

    const body = {
      query: req.body.query,
      files,
      band_map: parseJSON(req.body.band_map, undefined),
      boa_offset: req.body.boa_offset ? Number(req.body.boa_offset) : undefined,
      sar_vv_index: req.body.sar_vv_index ? Number(req.body.sar_vv_index) : undefined,
      tool_params: parseJSON(req.body.tool_params, {}),
    };
    for (const k of Object.keys(body)) if (body[k] === undefined) delete body[k];

    res.json(await mlPost("/analyze", body));
  } catch (e) {
    next(e);
  }
});

export default router;