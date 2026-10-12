import numpy as np

from tools.change import change_mask, ndvi


def test_no_change_gives_empty_mask():
    rng = np.random.default_rng(0)
    red = rng.uniform(0.05, 0.2, (64, 64)).astype("float32")
    nir = rng.uniform(0.3, 0.6, (64, 64)).astype("float32")
    n = ndvi(red, nir)
    mask, valid, _ = change_mask(n, n.copy(), min_area_px=1)
    assert mask.sum() == 0


def test_block_change_detected():
    red1 = np.full((64, 64), 0.1, dtype="float32")
    nir1 = np.full((64, 64), 0.5, dtype="float32")
    red2, nir2 = red1.copy(), nir1.copy()
    # Vegetation (NDVI ~0.67) turns into bare soil (NDVI ~0.0) in a 16x16 block
    red2[10:26, 10:26] = 0.4
    nir2[10:26, 10:26] = 0.4
    mask, valid, thr = change_mask(ndvi(red1, nir1), ndvi(red2, nir2), min_area_px=50)
    assert mask[10:26, 10:26].all()
    assert mask.sum() == 16 * 16


def test_small_noise_removed():
    n1 = np.full((64, 64), 0.5, dtype="float32")
    n2 = n1.copy()
    n2[0, 0] = 0.0  # single-pixel change
    n2[30:40, 30:40] = 0.0  # 100-pixel change
    mask, _, _ = change_mask(n1, n2, min_area_px=20)
    assert not mask[0, 0]
    assert mask[30:40, 30:40].all()