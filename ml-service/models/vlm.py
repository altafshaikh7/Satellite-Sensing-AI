"""
Mini-InternVL (base, no LoRA yet) for VQA on Sentinel-2 patches.
Loads in 4-bit on the GPU (bitsandbytes). Weights path: VLM_PATH env or weights/mini_internvl_base.
Nothing is faked: if weights, CUDA or the model cannot be loaded, ModelUnavailable is raised.
"""
import os
from pathlib import Path

import numpy as np
import rasterio
import torch
from PIL import Image
from rasterio.windows import Window

INPUT = 448                    # InternVL single-tile input size
PATCH = 1120                   # centre window read from the raster (about 11 km at 10 m)
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
DEFAULT_DIR = Path(__file__).resolve().parents[2] / "weights" / "mini_internvl_base"
_state = {"model": None, "tok": None}


class ModelUnavailable(RuntimeError):
    """The VLM cannot run here. The reason is written to the trace."""


def weights_dir() -> Path:
    return Path(os.getenv("VLM_PATH", str(DEFAULT_DIR)))


def _load():
    if _state["model"] is not None:
        return
    wdir = weights_dir()
    if not wdir.exists() or not list(wdir.glob("*.safetensors")):
        raise ModelUnavailable(f"Mini-InternVL weights not found at {wdir}. Set VLM_PATH or download the model.")
    if not torch.cuda.is_available():
        raise ModelUnavailable("CUDA GPU not available for the VLM.")

    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    qc = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                            bnb_4bit_quant_type="nf4")
    tok = AutoTokenizer.from_pretrained(str(wdir), trust_remote_code=True, use_fast=False)
    model = AutoModel.from_pretrained(
        str(wdir), quantization_config=qc, torch_dtype=torch.float16,
        low_cpu_mem_usage=True, trust_remote_code=True, device_map={"": 0},
    ).eval()
    _state.update(model=model, tok=tok)


def rgb_patch(path: str, bands=(2, 1, 0), size: int = PATCH) -> Image.Image:
    """
    Centre window of a 4-band stack (B02,B03,B04,B08), RGB = B04,B03,B02,
    percentile-stretched, resized to 448 px. Nodata (0) pixels are excluded from the stretch.
    """
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


def _pixel_values(img: Image.Image) -> torch.Tensor:
    x = (np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0 - MEAN) / STD
    t = torch.from_numpy(x.transpose(2, 0, 1)).unsqueeze(0)
    return t.to("cuda", dtype=torch.float16)


def answer(img: Image.Image, question: str, max_new_tokens: int = 128) -> str:
    _load()
    gen = dict(max_new_tokens=max_new_tokens, do_sample=False)
    text = _state["model"].chat(_state["tok"], _pixel_values(img), f"<image>\n{question}", gen)
    return str(text).strip()


def answer_pair(img_before: Image.Image, img_after: Image.Image, question: str,
                max_new_tokens: int = 128) -> str:
    """
    Two dates side by side, squeezed into one 448 px tile (single-tile InternVL input).
    The squeeze loses detail; this is a stated limitation.
    """
    canvas = Image.new("RGB", (INPUT * 2, INPUT))
    canvas.paste(img_before, (0, 0))
    canvas.paste(img_after, (INPUT, 0))
    canvas = canvas.resize((INPUT, INPUT), Image.BICUBIC)
    prompt = ("The left half is the earlier date and the right half is the later date. " + question)
    return answer(canvas, prompt, max_new_tokens=max_new_tokens)