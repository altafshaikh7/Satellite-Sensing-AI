import numpy as np

from tools.fusion import fuse

PARAMS = {"water_ndwi_min": 0.0, "sar_water_db_max": -18.0, "sar_built_db_min": -8.0}


def test_water_requires_both_optical_and_sar():
    green = np.full((8, 8), 0.2, dtype="float32")  # NDWI > 0 (water-like)
    nir = np.full((8, 8), 0.05, dtype="float32")
    red = np.full((8, 8), 0.05, dtype="float32")
    sar_dark = np.full((8, 8), -22.0, dtype="float32")
    sar_bright = np.full((8, 8), -5.0, dtype="float32")

    water_both = fuse(green, nir, red, sar_dark, PARAMS)["water"]
    water_optical_only = fuse(green, nir, red, sar_bright, PARAMS)["water"]
    assert water_both.all()
    assert not water_optical_only.any()


def test_built_up_bright_sar_low_ndvi():
    green = np.full((8, 8), 0.1, dtype="float32")
    nir = np.full((8, 8), 0.15, dtype="float32")  # NDVI ~0.2 boundary, use lower
    red = np.full((8, 8), 0.14, dtype="float32")
    sar = np.full((8, 8), -4.0, dtype="float32")
    r = fuse(green, nir, red, sar, PARAMS)
    assert r["built"].all()
    assert not r["water"].any()