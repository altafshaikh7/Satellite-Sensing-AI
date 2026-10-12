import os

import numpy as np
import rasterio
from rasterio.windows import Window


def check_file(path: str, declared: str | None = None) -> dict:
    """Check one file: format, CRS, band count, dtype, modality and SAR scale."""
    if not os.path.exists(path):
        return {"path": path, "ok": False, "errors": ["file not found"], "warnings": [],
                "modality": None, "sar_scale": None, "bands": 0, "dtype": None}

    errors: list[str] = []
    with rasterio.open(path) as src:
        if src.driver != "GTiff":
            errors.append(f"format '{src.driver}' not allowed, use GeoTIFF/TIFF")
        if src.crs is None:
            errors.append("missing CRS")
        count = src.count
        dtype = np.dtype(src.dtypes[0])
        w, h = min(256, src.width), min(256, src.height)
        sample = src.read(1, window=Window(0, 0, w, h), masked=True).astype("float64")

    vals = sample.compressed()
    if vals.size == 0:
        errors.append("no valid pixels in the sample window")

    detected = None
    if count >= 10:
        detected = "optical"                                   # multispectral (e.g. Sentinel-2)
    elif count in (3, 4) and np.issubdtype(dtype, np.integer):
        detected = "optical"                                   # RGB / RGBN integer imagery
    elif count <= 2 and np.issubdtype(dtype, np.floating) and vals.size and np.median(vals) < 0:
        detected = "sar"                                       # SAR backscatter in dB is negative

    modality = declared or detected
    if modality not in ("optical", "sar"):
        errors.append("cannot determine modality, declare 'optical' or 'sar'")
    if declared and detected and declared != detected:
        errors.append(f"declared '{declared}' but the file looks like '{detected}'")

    sar_scale = None
    if modality == "sar":
        if count not in (1, 2):
            errors.append("SAR file should have 1 band (VV) or 2 bands (VV, VH)")
        if vals.size:
            sar_scale = "db" if np.median(vals) < 0 else "linear"
    if modality == "optical" and count < 3:
        errors.append("optical file needs at least 3 bands")

    return {"path": path, "ok": not errors, "errors": errors, "warnings": [],
            "modality": modality, "sar_scale": sar_scale, "bands": count, "dtype": str(dtype)}