export default function QueryBox({ value, onChange, onSubmit, busy }) {
  return (
    <div className="field">
      <label>Query</label>
      <textarea rows={2} value={value} onChange={(e) => onChange(e.target.value)} />
      <button onClick={onSubmit} disabled={busy} style={{ marginTop: 8 }}>
        {busy ? "Analyzing..." : "Analyze"}
      </button>
    </div>
  );
}