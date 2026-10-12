import numpy as np


def pct(mask: np.ndarray, valid: np.ndarray) -> float:
    """Percent of valid pixels that are set in mask."""
    denom = int(valid.sum())
    return float(100.0 * (mask & valid).sum() / denom) if denom else 0.0


def iou(a: np.ndarray, b: np.ndarray) -> float | None:
    """Intersection over union. None when both masks are empty."""
    union = int((a | b).sum())
    return float((a & b).sum() / union) if union else None