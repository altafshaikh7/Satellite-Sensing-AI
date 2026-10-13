# Saves a Kaggle vlm_answer.json into outputs/vlm_answers/, adding the SHA-256 of the
# 448 px patch made from a GeoTIFF, so the VQA tool can match it to the same input.
# Usage (from satquery/): python scripts/save_vlm_answer.py <kaggle_json> <input_geotiff> <out_name>
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml-service"))
from preprocess.patch import patch_sha256  # noqa: E402

if len(sys.argv) != 4:
    sys.exit(__doc__)

src, tif, name = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
data = json.loads(src.read_text(encoding="utf-8"))
data["kind"] = "vqa"
data["image_sha256"] = patch_sha256(tif)
data["input_file"] = Path(tif).name

out = ROOT / "outputs" / "vlm_answers" / f"{name}.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, indent=2), encoding="utf-8")
print("saved:", out)
print("patch sha256:", data["image_sha256"])