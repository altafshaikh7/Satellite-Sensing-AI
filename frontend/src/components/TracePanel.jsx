export default function TracePanel({ result }) {
  const files = result.input_checks?.files || [];
  const pair = result.input_checks?.pair;
  return (
    <div className="card">
      <h3>Execution trace</h3>
      <p><b>Input configuration:</b> {result.input_config}</p>
      <p><b>Plan:</b> {result.plan.join(" → ")}</p>

      <table>
        <thead>
          <tr><th>Tool</th><th>Params</th><th>Status</th><th>ms</th></tr>
        </thead>
        <tbody>
          {result.tools.map((t) => (
            <tr key={t.name}>
              <td>{t.name}</td>
              <td><code>{JSON.stringify(t.params)}</code></td>
              <td className={t.status === "ok" ? "ok" : "bad"}>{t.status}</td>
              <td>{t.ms}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Input checks</h3>
      <ul>
        {files.map((f) => (
          <li key={f.path} style={{ fontSize: 13 }}>
            {f.path.split(/[\\/]/).pop()}: {f.ok ? <span className="ok">ok</span> : <span className="bad">failed</span>}
            {" "}({f.modality}, {f.bands} bands, {f.dtype})
          </li>
        ))}
        {pair && (
          <li style={{ fontSize: 13 }}>
            Pair: {pair.ok ? "ok" : "failed"}, overlap {pair.overlap}, same CRS {String(pair.same_crs)}, same grid {String(pair.same_grid)}
          </li>
        )}
      </ul>

      <h3>Alignment</h3>
      <p style={{ fontSize: 13 }}>
        {result.alignment ? `Applied: ${result.alignment.method}` : "Not needed (grids already match)."}
      </p>
      <p style={{ fontSize: 12, color: "#666" }}>Total time: {result.total_ms} ms</p>
    </div>
  );
}