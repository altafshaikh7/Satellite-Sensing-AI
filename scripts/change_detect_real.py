"""
Real raster change detection between two Sentinel-2 L2A stacks (B02, B03, B04, B08 at 10 m).
Optional cloud/shadow masking with the SCL band.

Usage (from satquery/):
  python scripts/change_detect_real.py <before.tif> <after.tif> <out_dir>
  python scripts/change_detect_real.py <before.tif> <after.tif> <out_dir> <scl_before.jp2> <scl_after.jp2>
"""
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml-service"))
from tools.change import change_mask, ndvi  # noqa: E402

BOA_OFFSET = -1000.0   # N0400+ baseline: DN = reflectance*10000 + 1000
SCALE = 10000.0
BAND_ORDER = ["B02", "B03", "B04", "B08"]
RED, NIR = 2, 3        # 0-based index inside BAND_ORDER
MIN_AREA_PX = 50
SCL_BAD = {3, 8, 9, 10}  # 3 = cloud shadow, 8/9 = cloud, 10 = thin cirrus


def read_stack(path):
    with rasterio.open(path) as src:
        if src.count != 4:
            sys.exit(f"{path}: expected 4 bands {BAND_ORDER}, found {src.count}")
        red = src.read(RED + 1)
        nir = src.read(NIR + 1)
        info = {
            "path": str(path), "crs": str(src.crs), "width": src.width, "height": src.height,
            "res": list(src.res), "transform": list(src.transform)[:6], "dtype": src.dtypes[0],
            "bands": BAND_ORDER,
            "nodata_fraction_red": float((red == 0).mean()),
            "nodata_fraction_nir": float((nir == 0).mean()),
        }
        return red, nir, info, src.transform, src.crs


def to_reflectance(dn):
    """DN -> reflectance. Nodata (DN == 0) becomes NaN."""
    refl = (dn.astype("float32") + BOA_OFFSET) / SCALE
    refl[dn == 0] = np.nan
    return refl


def scl_clear(scl_path, shape):
    """
    True where the scene is clear. SCL is 20 m, so it is upsampled x2
    (nearest neighbour) to the 10 m grid of the stack.
    """
    with rasterio.open(scl_path) as src:
        scl = src.read(1)
    scl = np.repeat(np.repeat(scl, 2, axis=0), 2, axis=1)
    scl = scl[:shape[0], :shape[1]]
    if scl.shape != shape:
        sys.exit(f"SCL shape {scl.shape} does not match image shape {shape} after upsampling.")
    return ~np.isin(scl, list(SCL_BAD))


def main():
    args = sys.argv[1:]
    if len(args) not in (3, 5):
        sys.exit(__doc__)
    before_p, after_p, out_dir = (Path(p) for p in args[:3])
    scl_b, scl_a = (args[3], args[4]) if len(args) == 5 else (None, None)
    out_dir.mkdir(parents=True, exist_ok=True)

    r1, n1, info1, t1, c1 = read_stack(before_p)
    r2, n2, info2, t2, c2 = read_stack(after_p)

    # Zero-data check: a band that is almost all nodata means a bad stack or source file.
    for name, arr in [("before red", r1), ("before nir", n1), ("after red", r2), ("after nir", n2)]:
        if (arr == 0).mean() > 0.99:
            sys.exit(f"{name}: 99%+ pixels are zero. Check the stacked file or the source band.")

    # Never resample silently. Stop if the grids differ.
    problems = []
    if str(c1) != str(c2):
        problems.append(f"CRS differs: {c1} vs {c2}")
    if (info1["width"], info1["height"]) != (info2["width"], info2["height"]):
        problems.append(f"shape differs: {info1['width']}x{info1['height']} vs {info2['width']}x{info2['height']}")
    if tuple(round(x, 6) for x in t1[:6]) != tuple(round(x, 6) for x in t2[:6]):
        problems.append("affine transform differs (grids not aligned)")
    if problems:
        print("STOP, inputs not aligned:")
        for p in problems:
            print(" -", p)
        sys.exit(1)

    with np.errstate(invalid="ignore", divide="ignore"):
        nd1 = ndvi(to_reflectance(r1), to_reflectance(n1))
        nd2 = ndvi(to_reflectance(r2), to_reflectance(n2))

    clear_fraction = None
    if scl_b and scl_a:
        clear = scl_clear(scl_b, nd1.shape) & scl_clear(scl_a, nd2.shape)
        nd1 = np.where(clear, nd1, np.nan)
        nd2 = np.where(clear, nd2, np.nan)
        clear_fraction = round(float(clear.mean()), 4)
        print("clear-sky fraction (both scenes):", clear_fraction)

    with np.errstate(invalid="ignore", divide="ignore"):
        mask, valid, thr = change_mask(nd1, nd2, MIN_AREA_PX)
        d = nd2 - nd1

    # Sanity checks: stop instead of reporting a silently wrong result.
    if valid.any():
        print("NDVI |diff| percentiles (1, 50, 99, 99.9):",
              np.percentile(np.abs(d[valid]), [1, 50, 99, 99.9]).round(3).tolist())
    if thr is not None and thr > 1.0:
        sys.exit(f"Otsu threshold {thr:.3f} is above 1.0. NDVI is still unstable. Check input reflectance.")

    valid_count = int(valid.sum())
    changed = int(mask.sum())
    inc = int((mask & (d > 0)).sum())
    dec = int((mask & (d < 0)).sum())
    changed_pct = 100.0 * changed / valid_count if valid_count else 0.0

    # Change mask as GeoTIFF, same CRS and transform as the before image.
    mask_path = out_dir / "change_mask.tif"
    profile = dict(driver="GTiff", height=info1["height"], width=info1["width"], count=1,
                   dtype="uint8", crs=c1, transform=t1, nodata=0, compress="deflate")
    with rasterio.open(mask_path, "w", **profile) as dst:
        dst.write(mask.astype("uint8"), 1)

    # Quick-look preview: NDVI before | NDVI after | after with changes in red (downsampled x8).
    s = 8

    def gray(a):
        a = np.nan_to_num(a[::s, ::s], nan=0.0)
        lo, hi = np.percentile(a, [2, 98])
        hi = hi if hi > lo else lo + 1e-6
        return np.clip((a - lo) / (hi - lo) * 255, 0, 255).astype("uint8")

    g1, g2 = gray(nd1), gray(nd2)
    overlay = np.stack([g2, g2, g2], -1)
    overlay[mask[::s, ::s]] = [255, 0, 0]
    panel = np.concatenate([np.stack([g1] * 3, -1), np.stack([g2] * 3, -1), overlay], axis=1)
    preview_path = out_dir / "change_preview.png"
    Image.fromarray(panel).save(preview_path)

    audit = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "method": "NDVI absolute difference (clipped to [-1, 1]), Otsu threshold, "
                  "connected components >= min_area_px"
                  + (", SCL cloud/shadow/cirrus mask" if scl_b else ""),
        "parameters": {"boa_offset": BOA_OFFSET, "scale": SCALE, "min_area_px": MIN_AREA_PX,
                       "band_order": BAND_ORDER, "red_index": RED, "nir_index": NIR,
                       "scl_bad_classes": sorted(SCL_BAD) if scl_b else None,
                       "scl_before": scl_b, "scl_after": scl_a},
        "before": info1,
        "after": info2,
        "checks": {"crs_match": True, "shape_match": True, "grid_match": True,
                   "zero_data_check": "passed", "threshold_sanity": "passed"},
        "results": {"otsu_threshold": thr, "valid_pixels": valid_count, "changed_pixels": changed,
                    "changed_pct": round(changed_pct, 3), "increase_px": inc, "decrease_px": dec,
                    "clear_sky_fraction": clear_fraction},
        "outputs": {"mask": str(mask_path), "preview": str(preview_path)},
        "limitations": [
            "NDVI only. Seasonal (phenological) change can appear as change.",
            "Cloud and shadow masking uses SCL only when SCL paths are given.",
            "Scenes from different seasons are not comparable for land-cover change.",
            "BOA offset fixed for N0400+ baseline. Check product metadata for other baselines.",
            "Pixels with very low brightness (denominator <= 0.02) are excluded as unstable NDVI.",
        ],
    }
    (out_dir / "audit.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")

    print(json.dumps(audit["results"], indent=2))
    print("outputs in:", out_dir)


if __name__ == "__main__":
    main()