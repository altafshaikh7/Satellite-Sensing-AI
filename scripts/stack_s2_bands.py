"""
Stack single-band Sentinel-2 files into one multi-band GeoTIFF.
Usage:
  python scripts/stack_s2_bands.py <out.tif> <band1> <band2> ...
Bands are written in the order given. Every band is resampled to the first band's grid.
"""
import sys

import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT

if len(sys.argv) < 3:
    sys.exit("usage: stack_s2_bands.py <out.tif> <band files in order>")

out, bands = sys.argv[1], sys.argv[2:]

with rasterio.open(bands[0]) as ref:
    h, w, crs, transform, dtype = ref.height, ref.width, ref.crs, ref.transform, ref.dtypes[0]

profile = dict(driver="GTiff", height=h, width=w, count=len(bands), dtype=dtype,
               crs=crs, transform=transform, compress="deflate")

with rasterio.open(out, "w", **profile) as dst:
    for i, band in enumerate(bands, start=1):
        with rasterio.open(band) as src, WarpedVRT(
            src, crs=crs, transform=transform, width=w, height=h,
            resampling=Resampling.bilinear,
        ) as vrt:
            dst.write(vrt.read(1), i)

print("wrote", out)