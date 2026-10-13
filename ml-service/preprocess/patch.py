# Center RGB patch from a 4-band Sentinel-2 stack (B02, B03, B04, B08).
# Torch-free, so both the VQA tool and the Kaggle export script can use it.
# Must stay identical to what the Kaggle notebook sees (same crop, same stretch, same resize).
import hashlib

import numpy as np
import rasterio
from PIL import Image
from rasterio.windows import Window

PATCH = 1120
INPUT = 448


def rgb_patch(path: str, bands=(2, 1, 0), size: int = PATCH) -> Image.Image:
    with rasterio.open(path) as src:
        s = min(size, src.height, src.width)
        r0, c0 = (src.height - s) // 2, (src.width - s) // 2
        arr = src.read(indexes=[b + 1 for b in bands], window=Window(c0, r0, s, s)).astype("float32")
    out = np.zeros((s, s, 3), dtype=np.float32)
    for i in range(3):
        ch = arr[i]
        ok = ch > 0
        lo, hi = np.percentile(ch[ok], [2, 98]) if ok.any() else (0.0, 1.0)
        hi = hi if hi > lo else lo + 1.0
        out[..., i] = np.clip((ch - lo) / (hi - lo), 0.0, 1.0)
    return Image.fromarray((out * 255).astype("uint8"), "RGB").resize((INPUT, INPUT), Image.BICUBIC)


def patch_sha256(path: str) -> str:
    """SHA-256 of the 448 px PNG bytes of the patch, as saved by the export script."""
    import io
    buf = io.BytesIO()
    rgb_patch(path).save(buf, format="PNG")
    return hashlib.sha256(buf.getvalue()).hexdigest()