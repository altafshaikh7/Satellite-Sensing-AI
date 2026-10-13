"""
Runs the tool plan from controller/router.py.
Every call is validated against the registry, timed and logged.
A tool that cannot run reports status 'unavailable' with the reason. No output is invented.
"""
import time

import numpy as np
import rasterio

from controller.vlm_tools import ToolUnavailable, tool_change_vqa, tool_vqa
from registry.registry import ParamError, validate_params
from tools import change, fusion
from tools.stats import iou, pct

SCALE = 10000.0


def read_reflectance(path: str, indices: dict[str, int], boa_offset: float) -> dict[str, np.ndarray]:
    """L2A DN -> reflectance: (DN + BOA_OFFSET) / 10000. Nodata (DN == 0) becomes NaN."""
    out: dict[str, np.ndarray] = {}
    with rasterio.open(path) as src:
        for name, idx in indices.items():
            if not 0 <= idx < src.count:
                raise ValueError(f"band index {idx} for '{name}' is outside 0..{src.count - 1} in {path}")
            dn = src.read(idx + 1)
            refl = (dn.astype("float32") + boa_offset) / SCALE
            refl[dn == 0] = np.nan
            out[name] = refl
    return out


def read_band(path: str, idx: int) -> np.ndarray:
    with rasterio.open(path) as src:
        if not 0 <= idx < src.count:
            raise ValueError(f"band index {idx} is outside 0..{src.count - 1} in {path}")
        arr = src.read(idx + 1).astype("float32")
        if src.nodata is not None:
            arr = np.where(arr == src.nodata, np.nan, arr)
    return arr


def tool_change(p: dict, ctx: dict) -> dict:
    bm = ctx["band_map"]
    spec = {"red": bm["red"], "nir": bm["nir"]}
    a = read_reflectance(ctx["before"], spec, ctx["boa_offset"])
    b = read_reflectance(ctx["after"], spec, ctx["boa_offset"])
    with np.errstate(invalid="ignore", divide="ignore"):
        nd1 = change.ndvi(a["red"], a["nir"])
        nd2 = change.ndvi(b["red"], b["nir"])
        mask, valid, thr = change.change_mask(nd1, nd2, p["min_area_px"])
        d = nd2 - nd1
    valid_px = int(valid.sum())
    changed = int(mask.sum())
    return {
        "mask": mask,
        "valid_px": valid_px,
        "changed_px": changed,
        "changed_pct": 100.0 * changed / valid_px if valid_px else 0.0,
        "increase_px": int((mask & (d > 0)).sum()),
        "decrease_px": int((mask & (d < 0)).sum()),
        "threshold": thr,
    }


def tool_fusion(p: dict, ctx: dict) -> dict:
    if ctx["optical"] is None or ctx["sar"] is None:
        raise ValueError("fusion needs one optical and one SAR image")
    bm = ctx["band_map"]
    o = read_reflectance(ctx["optical"], {"green": bm["green"], "nir": bm["nir"], "red": bm["red"]},
                         ctx["boa_offset"])
    sar = read_band(ctx["sar"], ctx["sar_vv_index"])
    if ctx["sar_scale"] == "linear":
        sar = 10 * np.log10(np.clip(sar, 1e-6, None))
    with np.errstate(invalid="ignore", divide="ignore"):
        r = fusion.fuse(o["green"], o["nir"], o["red"], sar, p)
    valid = r["valid"]
    return {
        "water": r["water"],
        "built": r["built"],
        "valid": valid,
        "water_pct": pct(r["water"], valid),
        "built_pct": pct(r["built"], valid),
        "agreement_iou": iou(r["opt_water"], r["sar_water"]),
    }


def tool_grounding(p: dict, ctx: dict) -> dict:
    raise ToolUnavailable("grounding: not connected yet. Planned next with Mini-InternVL box output.")


TOOLS = {
    "change": tool_change,
    "fusion": tool_fusion,
    "vqa": tool_vqa,
    "grounding": tool_grounding,
    "change_vqa": tool_change_vqa,
}


def run_plan(plan: list[str], ctx: dict, tool_params: dict) -> tuple[dict, list[dict]]:
    results: dict[str, dict] = {}
    log: list[dict] = []
    for name in plan:
        t0 = time.time()
        requested = tool_params.get(name, {})
        params: dict = {}
        try:
            params = validate_params(name, requested)
            out = TOOLS[name](params, ctx)
            status = "ok"
        except ToolUnavailable as e:
            status, out = "unavailable", {"error": str(e)}
        except ParamError as e:
            status, out = "rejected", {"error": str(e)}
        except Exception as e:  # noqa: BLE001 - every failure is reported in the trace
            status, out = "error", {"error": f"{type(e).__name__}: {e}"}
        results[name] = out
        log.append({
            "name": name,
            "requested_params": requested,
            "params": params,
            "status": status,
            "ms": round((time.time() - t0) * 1000),
        })
    return results, log