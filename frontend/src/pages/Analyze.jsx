// Analysis page: owns the state and calls the backend.
import { useState } from "react";
import HeroSection from "../sections/HeroSection.jsx";
import InputSection from "../sections/InputSection.jsx";
import MapSection from "../sections/MapSection.jsx";
import { analyze } from "../api.js";

export default function Analyze() {
  const [before, setBefore] = useState(null);
  const [after, setAfter] = useState(null);
  const [query, setQuery] = useState("Where did the vegetation change?");
  const [status, setStatus] = useState({ state: "idle", message: "" });
  const [result, setResult] = useState(null);

  const overlay = (() => {
    const m = result?.evidence?.masks?.find((x) => x.image_url);
    return m ? { url: m.image_url, bounds: m.bounds } : null;
  })();

  async function run() {
    if (!before || !after) return setStatus({ state: "error", message: "Please choose both GeoTIFF images." });
    if (!query.trim()) return setStatus({ state: "error", message: "Please enter a query." });

    const fd = new FormData();
    fd.append("query", query.trim());
    fd.append("images", before);
    fd.append("images", after);
    fd.append("modalities", "optical,optical");

    setResult(null);
    setStatus({ state: "running", message: "Analysis running (full scene takes 30-60 s)..." });
    try {
      const data = await analyze(fd);
      setResult(data);
      setStatus({ state: "done", message: `Done. Run ${data.run_id}` });
    } catch (e) {
      setStatus({ state: "error", message: e.message });
    }
  }

  return (
    <>
      <HeroSection />
      <div className="two-col">
        <InputSection
          before={before} after={after} onBefore={setBefore} onAfter={setAfter}
          query={query} onQuery={setQuery} onSubmit={run} busy={status.state === "running"}
          status={status} result={result}
        />
        <MapSection overlay={overlay} />
      </div>
    </>
  );
}