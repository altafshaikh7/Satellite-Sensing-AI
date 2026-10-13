export default function ResultPanel({ result }) {
  const stats = result.evidence?.stats || {};
  const mask = result.evidence?.masks?.[0];
  return (
    <div className="card">
      <h3>Answer</h3>
      <p>{result.answer}</p>

      <h3>Statistics</h3>
      <table>
        <tbody>
          {Object.entries(stats).map(([k, v]) => (
            <tr key={k}>
              <td>{k}</td>
              <td>{String(v)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {mask && (
        <p>
          <span className="legend" />
          Red = changed pixels ({mask.name}). Mask file: <a href={mask.url} target="_blank" rel="noreferrer">GeoTIFF</a>
        </p>
      )}

      <h3>Confidence</h3>
      <pre>{JSON.stringify(result.confidence, null, 2)}</pre>

      <h3>Limitations</h3>
      <ul>
        {result.limitations.map((x) => (
          <li key={x} style={{ fontSize: 13 }}>{x}</li>
        ))}
      </ul>

      <p>
        <a href={result.report_url} target="_blank" rel="noreferrer">Open full HTML report</a>
      </p>
    </div>
  );
}