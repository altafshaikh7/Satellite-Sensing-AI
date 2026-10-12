import pytest
import rasterio
from rasterio.transform import from_origin


@pytest.fixture
def write_raster(tmp_path):
    def _write(name, data, transform=None, crs="EPSG:32643"):
        count, h, w = data.shape
        t = transform or from_origin(500000, 1500000, 10, 10)
        p = tmp_path / name
        with rasterio.open(p, "w", driver="GTiff", height=h, width=w, count=count,
                           dtype=data.dtype, crs=crs, transform=t) as dst:
            dst.write(data)
        return str(p)
    return _write