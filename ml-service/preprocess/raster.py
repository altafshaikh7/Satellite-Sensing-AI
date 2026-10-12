import numpy as np
import rasterio


def read_bands(path: str, indices: dict[str, int]) -> dict[str, np.ndarray]:
    """Read named bands by 0-based index. Nodata pixels become NaN."""
    out: dict[str, np.ndarray] = {}
    with rasterio.open(path) as src:
        for name, idx in indices.items():
            if not (0 <= idx < src.count):
                raise ValueError(f"band index {idx} for '{name}' is outside 0..{src.count - 1}")
            arr = src.read(idx + 1).astype("float32")
            if src.nodata is not None:
                arr = np.where(arr == src.nodata, np.nan, arr)
            out[name] = arr
    return out


def to_reflectance(arr: np.ndarray) -> np.ndarray:
    """Sentinel-2 L2A stores reflectance x10000. Values above 2 are treated as scaled."""
    finite = arr[np.isfinite(arr)]
    if finite.size and finite.max() > 2.0:
        return arr / 10000.0
    return arr