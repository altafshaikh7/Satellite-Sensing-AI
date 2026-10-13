import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject


def align_to_reference(ref_path: str, src_path: str, out_path: str) -> str:
    """
    Reproject and resample src onto the CRS, transform and shape of ref.
    Writes a new file. The source file is never modified.
    """
    with rasterio.open(ref_path) as ref, rasterio.open(src_path) as src:
        if ref.crs is None or src.crs is None:
            raise ValueError("cannot align: missing CRS in one of the files")
        profile = src.profile.copy()
        profile.update(driver="GTiff", crs=ref.crs, transform=ref.transform,
                       width=ref.width, height=ref.height, compress="deflate")
        with rasterio.open(out_path, "w", **profile) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=ref.transform,
                    dst_crs=ref.crs,
                    src_nodata=src.nodata,
                    dst_nodata=src.nodata,
                    resampling=Resampling.bilinear,
                )
    return out_path