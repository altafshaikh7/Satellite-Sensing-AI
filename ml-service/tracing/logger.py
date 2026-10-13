import json

from app.config import OUTPUTS_DIR


def save_trace(trace: dict) -> str:
    path = OUTPUTS_DIR / "traces" / f"{trace['run_id']}.json"
    path.write_text(json.dumps(trace, indent=2, default=str), encoding="utf-8")
    return str(path)