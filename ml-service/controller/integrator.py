"""
Combines tool outputs into one answer, map evidence and confidence notes.
Masks are written as GeoTIFF with the reference image's CRS and transform.
"""
import numpy as np
import rasterio

from app.config import OUTPUTS_DIR
from tracing.overlay import mask_to_overlay


def _write_mask(ref_path: str, arr: np.ndarray, run_id: str, name: str) -> str:
    with rasterio.open(ref_path) as ref:
        if arr.shape != (ref.height, ref.width):
            raise ValueError(f"mask shape {arr.shape} does not match reference {ref.height}x{ref.width}")
        profile = dict(driver="GTiff", height=ref.height, width=ref.width, count=1, dtype="uint8",
                       crs=ref.crs, transform=ref.transform, nodata=0, compress="deflate")
    out = OUTPUTS_DIR / "masks" / f"{run_id}_{name}.tif"
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(arr.astype("uint8"), 1)
    return f"/outputs/masks/{out.name}"


def build(results: dict, ctx: dict, run_id: str):
    parts: list[str] = []
    masks: list[dict] = []
    stats: dict = {}
    confidence: dict = {}

    for name, r in results.items():
        if "error" in r:
            parts.append(f"{name}: {r['error']}")
            continue

        if name == "change":
            url = _write_mask(ctx["ref"], r["mask"], run_id, "change")
            png = OUTPUTS_DIR / "masks" / f"{run_id}_change.png"
            ov = mask_to_overlay(OUTPUTS_DIR / "masks" / f"{run_id}_change.tif", str(png))
            masks.append({"name": "change", "url": url, "legend": {"1": "changed"},
                          "image_url": f"/outputs/masks/{png.name}", "bounds": ov["bounds"]})
            stats["change_changed_pct"] = round(r["changed_pct"], 3)
            stats["change_valid_px"] = r["valid_px"]
            stats["change_increase_px"] = r["increase_px"]
            stats["change_decrease_px"] = r["decrease_px"]
            stats["change_threshold_ndvi"] = None if r["threshold"] is None else round(float(r["threshold"]), 4)
            parts.append(
                f"About {r['changed_pct']:.2f}% of valid pixels changed between the two dates "
                f"(NDVI difference, Otsu threshold). {r['decrease_px']} changed pixels lost NDVI and "
                f"{r['increase_px']} gained it. A loss can be seasonal browning rather than land-cover change."
            )
            confidence["change"] = "not a calibrated probability. See threshold and limitations."

        elif name == "fusion":
            arr = np.zeros(r["valid"].shape, dtype=np.uint8)
            arr[r["water"]] = 1
            arr[r["built"]] = 2
            url = _write_mask(ctx["ref"], arr, run_id, "fusion")
            masks.append({"name": "fusion", "url": url, "legend": {"1": "water", "2": "built-up"}})
            stats["fusion_water_pct"] = round(r["water_pct"], 3)
            stats["fusion_built_pct"] = round(r["built_pct"], 3)
            iou_val = r["agreement_iou"]
            confidence["fusion_water_agreement_iou"] = None if iou_val is None else round(float(iou_val), 3)
            parts.append(
                f"Water covers {r['water_pct']:.2f}% and built-up {r['built_pct']:.2f}% of valid pixels. "
                "Water = optical NDWI high AND SAR VV low. Built-up = SAR VV high AND NDVI low."
            )

        else:  # vqa, grounding, change_vqa return text answers
            parts.append(str(r.get("answer", "")))

    answer = " ".join(p for p in parts if p) or "No tool produced an output."
    evidence = {"masks": masks, "stats": stats}
    limitations = [
        "NDVI and NDWI thresholds are rule-based baselines, not trained models.",
        "No cloud or shadow mask is applied in this run. Use low-cloud scenes or the SCL script.",
        "Scenes from different seasons are not comparable for land-cover change.",
        "BOA offset is taken from the request (default -1000 for N0400 and later baselines).",
    ]
    return answer, evidence, confidence, limitations