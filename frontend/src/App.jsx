import { useMemo, useState } from "react";
import UploadPanel from "./components/UploadPanel.jsx";
import QueryBox from "./components/QueryBox.jsx";
import MapView from "./components/MapView.jsx";
import ResultPanel from "./components/ResultPanel.jsx";
import TracePanel from "./components/TracePanel.jsx";
import "./index.css";

function errorText(data) {
  if (!data) return "Unknown error";
  if (typeof data.error === "string") return data.error;
  if (typeof data.detail === "string") return data.detail;
  return JSON.stringify(data.detail ?? data).slice(0, 400);
}

export default function App() {
  const [before, setBefore] = useState(null);
  const [after, setAfter] = useState(null);
  const [query, setQuery] = useState("Where did the vegetation change?");
  const [status, setStatus] = useState({ state: "idle", message: "" });
  const [result, setResult] = useState(null);

  const overlay = useMemo(() => {
    const m = result?.evidence?.masks?.find((x) => x.image_url);
    return m ? { url: m.image_url, bounds: m.bounds } : null;
  }, [result]);

  async function analyze() {
    if (!before || !after) {
      setStatus({ state: "error", message: "Choose both GeoTIFF images." });
      return;
    }
    if (!query.trim()) {
      setStatus({ state: "error", message: "Write a query." });
      return;
    }
    const fd = new FormData();
    fd.append("query", query.trim());
    fd.append("images", before);
    fd.append("images", after);
    fd.append("modalities", "optical,optical");

    setResult(null);
    setStatus({ state: "running", message: "Running analysis. A full scene takes 30-60 s..." });
    try {
      const res = await fetch("/api/query", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(errorText(data));
      setResult(data);
      setStatus({ state: "done", message: `Done. Run ${data.run_id}` });
    } catch (e) {
      setStatus({ state: "error", message: e.message });
    }
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>SatQuery AI</h1>
        <UploadPanel before={before} after={after} onBefore={setBefore} onAfter={setAfter} />
        <QueryBox value={query} onChange={setQuery} onSubmit={analyze} busy={status.state === "running"} />
        <p className={`status ${status.state}`}>{status.message}</p>
        {result && <ResultPanel result={result} />}
        {result && <TracePanel result={result} />}
      </aside>
      <main className="map">
        <MapView overlay={overlay} />
      </main>
    </div>
  );
}