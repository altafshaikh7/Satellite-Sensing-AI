import numpy as np
from scipy import ndimage
from skimage.filters import threshold_otsu


def ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    NDVI = (NIR - Red) / (NIR + Red).
    Negative reflectance is clipped to 0. Pixels with denominator <= 0.02 are NaN
    (NDVI is unstable there). Output is clipped to [-1, 1].
    """
    red = np.clip(red, 0, None)
    nir = np.clip(nir, 0, None)
    denom = nir + red
    with np.errstate(invalid="ignore", divide="ignore"):
        out = (nir - red) / denom
    out = np.where(denom > 0.02, out, np.nan)
    return np.clip(out, -1.0, 1.0)


def change_mask(ndvi_t1: np.ndarray, ndvi_t2: np.ndarray, min_area_px: int = 50):
    """
    Absolute NDVI difference, Otsu threshold, then drop small connected components.
    Returns (change_mask, valid_mask, threshold).
    Baseline only: seasonal (phenological) change can also appear as change.
    """
    valid = np.isfinite(ndvi_t1) & np.isfinite(ndvi_t2)
    if not valid.any():
        raise ValueError("no valid pixels in the overlapping area")

    diff = np.where(valid, np.abs(ndvi_t2 - ndvi_t1), 0.0).astype("float32")
    vals = diff[valid]
    if vals.max() - vals.min() < 1e-9:
        return np.zeros(valid.shape, dtype=bool), valid, None

    thr = float(threshold_otsu(vals))
    mask = valid & (diff > thr)

    labels, n = ndimage.label(mask)
    if n == 0:
        return mask, valid, thr

    # Pixel count per component. bincount keeps memory low on full-scene rasters.
    sizes = np.bincount(labels.ravel())
    keep = np.zeros(sizes.shape[0], dtype=bool)
    keep[1:] = sizes[1:] >= min_area_px
    keep[0] = False

    return keep[labels], valid, thr