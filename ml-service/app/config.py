import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # satquery/
OUTPUTS_DIR = Path(os.getenv("OUTPUTS_DIR", ROOT / "outputs"))

for _sub in ("traces", "reports", "masks", "aligned"):
    (OUTPUTS_DIR / _sub).mkdir(parents=True, exist_ok=True)