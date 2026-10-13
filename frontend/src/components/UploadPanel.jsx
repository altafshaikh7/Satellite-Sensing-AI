export default function UploadPanel({ before, after, onBefore, onAfter }) {
  return (
    <div>
      <div className="field">
        <label>Image 1, earlier (GeoTIFF)</label>
        <input type="file" accept=".tif,.tiff" onChange={(e) => onBefore(e.target.files[0] || null)} />
      </div>
      <div className="field">
        <label>Image 2, later (GeoTIFF)</label>
        <input type="file" accept=".tif,.tiff" onChange={(e) => onAfter(e.target.files[0] || null)} />
      </div>
      {before && after && <p className="muted" style={{ fontSize: 12 }}>{before.name} → {after.name}</p>}
    </div>
  );
}