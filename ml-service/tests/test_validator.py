import numpy as np
from rasterio.transform import from_origin

from validator import band_check, geo_checker


def test_multispectral_detected_as_optical(write_raster):
    data = np.random.default_rng(0).integers(0, 3000, (13, 64, 64), dtype="uint16")
    res = band_check.check_file(write_raster("s2.tif", data))
    assert res["ok"] is True
    assert res["modality"] == "optical"


def test_declared_sar_on_optical_file_fails(write_raster):
    data = np.random.default_rng(1).integers(0, 3000, (13, 32, 32), dtype="uint16")
    res = band_check.check_file(write_raster("s2b.tif", data), declared="sar")
    assert res["ok"] is False


def test_sar_db_file_detected(write_raster):
    data = np.random.default_rng(2).uniform(-25, -5, (1, 64, 64)).astype("float32")
    res = band_check.check_file(write_raster("s1.tif", data))
    assert res["ok"] is True
    assert res["modality"] == "sar"
    assert res["sar_scale"] == "db"


def test_overlapping_pair_passes(write_raster):
    # Shift 10% of the 640 m width, so ~90% of the area overlaps
    data = np.zeros((4, 64, 64), dtype="uint16")
    pa = write_raster("a.tif", data)
    pb = write_raster("b.tif", data, transform=from_origin(500000 + 64 * 10 * 0.1, 1500000, 10, 10))
    res = geo_checker.check_pair(pa, pb)
    assert res["ok"] is True
    assert res["same_crs"] is True


def test_low_overlap_pair_fails(write_raster):
    data = np.zeros((1, 32, 32), dtype="uint16")
    pa = write_raster("a.tif", data)
    pb = write_raster("b.tif", data, transform=from_origin(600000, 1500000, 10, 10))
    res = geo_checker.check_pair(pa, pb)
    assert res["ok"] is False