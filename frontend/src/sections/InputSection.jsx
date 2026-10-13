// Left column: image upload, query input, status and results.
import UploadPanel from "../components/UploadPanel.jsx";
import QueryBox from "../components/QueryBox.jsx";
import ResultPanel from "../components/ResultPanel.jsx";
import TracePanel from "../components/TracePanel.jsx";

export default function InputSection({
  before, after, onBefore, onAfter,
  query, onQuery, onSubmit, busy,
  status, result,
}) {
  return (
    <div className="panel">
      <UploadPanel before={before} after={after} onBefore={onBefore} onAfter={onAfter} />
      <QueryBox value={query} onChange={onQuery} onSubmit={onSubmit} busy={busy} />
      <p className={`status ${status.state}`}>{status.message}</p>
      {result && <ResultPanel result={result} />}
      {result && <TracePanel result={result} />}
    </div>
  );
}