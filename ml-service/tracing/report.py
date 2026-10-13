import html
import json

from app.config import OUTPUTS_DIR


def write_report(trace: dict) -> str:
    run_id = trace["run_id"]
    rows = "".join(
        f"<tr><td>{html.escape(t['name'])}</td>"
        f"<td>{html.escape(json.dumps(t['params']))}</td>"
        f"<td>{html.escape(t['status'])}</td><td>{t['ms']}</td></tr>"
        for t in trace["tools"]
    )
    limits = "".join(f"<li>{html.escape(x)}</li>" for x in trace["limitations"])
    masks = "".join(
        f"<li>{html.escape(m['name'])}: <a href='{html.escape(m['url'])}'>{html.escape(m['url'])}</a></li>"
        for m in trace["evidence"]["masks"]
    ) or "<li>none</li>"
    align = html.escape(json.dumps(trace["alignment"], indent=2, default=str))
    doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>SatQuery report {run_id}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 20px auto; padding: 0 16px; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1px solid #ccc; padding: 6px; text-align: left; vertical-align: top; }}
pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
</style></head><body>
<h1>SatQuery AI report</h1>
<p><b>Run:</b> {run_id}</p>
<p><b>Query:</b> {html.escape(trace['query'])}</p>
<p><b>Input configuration:</b> {html.escape(trace['input_config'])}</p>
<h2>Answer</h2><p>{html.escape(trace['answer'])}</p>
<h2>Evidence (masks)</h2><ul>{masks}</ul>
<h2>Statistics</h2><pre>{html.escape(json.dumps(trace['evidence']['stats'], indent=2, default=str))}</pre>
<h2>Confidence</h2><pre>{html.escape(json.dumps(trace['confidence'], indent=2, default=str))}</pre>
<h2>Limitations</h2><ul>{limits}</ul>
<h2>Tool execution</h2>
<table><tr><th>Tool</th><th>Params</th><th>Status</th><th>ms</th></tr>{rows}</table>
<h2>Input checks</h2><pre>{html.escape(json.dumps(trace['input_checks'], indent=2, default=str))}</pre>
<h2>Alignment</h2><pre>{align}</pre>
</body></html>"""
    path = OUTPUTS_DIR / "reports" / f"{run_id}.html"
    path.write_text(doc, encoding="utf-8")
    return str(path)