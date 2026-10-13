import numpy as np
import rasterio
from PIL import Image
from rasterio.warp import transform_bounds


def mask_to_overlay(mask_tif: str, png_out: str, max_side: int = 1200) -> dict:
    """
    Convert a uint8 mask GeoTIFF into a transparent RGBA PNG (changed pixels in red)
    and return its bounds in WGS84 as [[south, west], [north, east]] for Leaflet.
    The PNG is downsampled so the browser can load it quickly.
    """
    with rasterio.open(mask_tif) as src:
        arr = src.read(1)
        west, south, east, north = transform_bounds(src.crs, "EPSG:4326", *src.bounds)

    step = max(1, int(np.ceil(max(arr.shape) / max_side)))
    small = arr[::step, ::step]
    rgba = np.zeros((*small.shape, 4), dtype=np.uint8)
    hit = small == 1
    rgba[hit] = [255, 0, 0, 180]
    Image.fromarray(rgba, "RGBA").save(png_out)
    return {"south": south, "west": west, "north": north, "east": east,
            "bounds": [[south, west], [north, east]], "downsample": step}