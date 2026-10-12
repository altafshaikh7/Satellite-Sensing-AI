import numpy as np


def fuse(green, nir, red, sar_vv_db, p: dict) -> dict:
    """
    Rule-based optical-SAR extraction. No training needed.
    water : optical NDWI high AND SAR VV low (dark on radar)
    built : SAR VV high (double-bounce) AND low NDVI, outside water
    """
    with np.errstate(invalid="ignore", divide="ignore"):
        valid = np.isfinite(green) & np.isfinite(nir) & np.isfinite(red) & np.isfinite(sar_vv_db)
        ndwi = (green - nir) / (green + nir + 1e-6)
        ndvi = (nir - red) / (nir + red + 1e-6)
        opt_water = valid & (ndwi > p["water_ndwi_min"])
        sar_water = valid & (sar_vv_db < p["sar_water_db_max"])
        water = opt_water & sar_water
        built = valid & (sar_vv_db > p["sar_built_db_min"]) & (ndvi < 0.2) & ~water
    return {"water": water, "built": built, "valid": valid,
            "opt_water": opt_water, "sar_water": sar_water}