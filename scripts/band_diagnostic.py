import rasterio

with rasterio.open(r"outputs\change_T30TVL_scl\change_mask.tif") as m:
    mask = m.read(1).astype(bool)

for name, p in [("before", r"data\samples\optical_sar\s2_before.tif"),
                ("after",  r"data\samples\optical_sar\s2_after.tif")]:
    with rasterio.open(p) as s:
        for i, band in enumerate(["B02", "B03", "B04", "B08"], start=1):
            a = s.read(i).astype("float32")
            ok = a > 0
            print(name, band,
                  "changed:", round(float(a[mask & ok].mean())),
                  "unchanged:", round(float(a[~mask & ok].mean())))