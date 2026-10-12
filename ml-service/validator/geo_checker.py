import rasterio
from rasterio.warp import transform_bounds
from shapely.geometry import box

MIN_OVERLAP = 0.5  # fraction of the smaller image that must overlap


def check_pair(path_a: str, path_b: str) -> dict:
    """Check CRS, grid and spatial overlap of two rasters."""
    errors: list[str] = []
    warnings: list[str] = []
    with rasterio.open(path_a) as a, rasterio.open(path_b) as b:
        if a.crs is None or b.crs is None:
            return {"ok": False, "errors": ["missing CRS in one or both files"], "warnings": [],
                    "overlap": 0.0, "same_crs": False, "same_grid": False}
        bb = transform_bounds(b.crs, a.crs, *b.bounds)
        A = box(*a.bounds)
        B = box(*bb)
        small = min(A.area, B.area)
        overlap = float(A.intersection(B).area / small) if small > 0 else 0.0
        same_crs = a.crs == b.crs
        same_grid = same_crs and a.transform == b.transform and (a.width, a.height) == (b.width, b.height)

    if overlap < MIN_OVERLAP:
        errors.append(f"bounding-box overlap {overlap:.2f} is below {MIN_OVERLAP}")
    if not same_crs:
        warnings.append("different CRS: second image will be reprojected to the first CRS")
    elif not same_grid:
        warnings.append("same CRS but different grid: second image will be resampled")

    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "overlap": round(overlap, 3), "same_crs": same_crs, "same_grid": same_grid}