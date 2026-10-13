// Right column: Leaflet map card with the analysis overlay.
import MapView from "../components/MapView.jsx";

export default function MapSection({ overlay }) {
  return (
    <div className="map-box">
      <MapView overlay={overlay} />
    </div>
  );
}