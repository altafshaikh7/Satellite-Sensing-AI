import { useEffect } from "react";
import { MapContainer, TileLayer, ImageOverlay, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

function FitTo({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [20, 20] });
  }, [bounds, map]);
  return null;
}

export default function MapView({ overlay }) {
  return (
    <MapContainer center={[20, 0]} zoom={2} style={{ height: "100%", width: "100%" }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      {overlay && (
        <>
          <ImageOverlay url={overlay.url} bounds={overlay.bounds} opacity={0.8} />
          <FitTo bounds={overlay.bounds} />
        </>
      )}
    </MapContainer>
  );
}