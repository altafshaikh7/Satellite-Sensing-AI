"""
Direct VLM test on one Sentinel-2 scene. Writes the input patch to outputs/vlm_test_patch.png.
Usage (from satquery/):  python scripts/test_vlm.py [optional_image.tif] [optional question]
"""
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml-service"))
from models import vlm  # noqa: E402

img_path = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "data/samples/optical_sar/s2_optical.tif")
question = sys.argv[2] if len(sys.argv) > 2 else "Describe the land cover and major objects visible in this image."

patch = vlm.rgb_patch(img_path)
out = ROOT / "outputs" / "vlm_test_patch.png"
patch.save(out)
print("patch saved:", out)

t0 = time.time()
print("answer:", vlm.answer(patch, question))
print("seconds:", round(time.time() - t0, 1))
if torch.cuda.is_available():
    print("peak VRAM (GB):", round(torch.cuda.max_memory_allocated() / 1e9, 2))