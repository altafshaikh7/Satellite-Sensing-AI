# VLM-backed tools. Answers come from a saved Kaggle run (pre-computed).
# A tool returns "unavailable" when no saved answer matches the request.
import json
from pathlib import Path

from preprocess.patch import patch_sha256

ANSWER_DIR = Path(__file__).resolve().parents[2] / "outputs" / "vlm_answers"


class ToolUnavailable(RuntimeError):
    pass


def _load_saved(kind: str) -> list[dict]:
    if not ANSWER_DIR.exists():
        raise ToolUnavailable(f"{kind}: no saved VLM answers in {ANSWER_DIR}")
    rows = []
    for p in sorted(ANSWER_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("kind", "vqa") == kind:
            rows.append(data)
    if not rows:
        raise ToolUnavailable(f"no saved {kind} answer found in {ANSWER_DIR}")
    return rows


def tool_vqa(p: dict, ctx: dict) -> dict:
    if p["adapter"] != "none":
        raise ToolUnavailable(f"LoRA adapter '{p['adapter']}' is not trained yet. Use adapter 'none'.")
    rows = _load_saved("vqa")
    # Saved answers are valid only for the exact patch and question they were made for.
    image_hash = patch_sha256(ctx["before"])
    for r in rows:
        if r.get("image_sha256") == image_hash and r.get("question", "").strip() == ctx["query"].strip():
            return {
                "answer": r["answer"],
                "adapter": r.get("adapter", "none"),
                "source": "Kaggle notebook (saved run)",
                "model": r.get("model"),
                "gpu": r.get("gpu"),
                "inference_seconds": r.get("seconds"),
                "peak_vram_gb": r.get("peak_vram_gb"),
            }
    raise ToolUnavailable(
        "no saved Kaggle answer for this image patch and question. "
        "Run the Kaggle notebook on this patch to create one."
    )


def tool_change_vqa(p: dict, ctx: dict) -> dict:
    raise ToolUnavailable("not connected yet. Needs a saved Kaggle change-VQA answer.")


def tool_grounding(p: dict, ctx: dict) -> dict:
    raise ToolUnavailable("not connected yet. Needs Mini-InternVL box output saved from Kaggle.")