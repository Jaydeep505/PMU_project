"""
Validation report generator.

Produces a self-contained HTML validation report from the campaign rows:
executive summary, per-parameter spec table with Cpk and yield, distribution
stats, and a shmoo grid. Charts are drawn as inline SVG so the report is a
single file with no external dependencies.

Optional PDF: if `weasyprint` is installed, render_pdf() converts the HTML.
HTML alone is enough for a portfolio; PDF is a nice-to-have.

HONEST FRAMING (printed in the report header): data source is stated
explicitly -- real measurements vs. modeled/out-of-scope -- so nothing is
presented as something it is not.
"""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

from . import analysis


def _svg_bar_chart(title, labels, values, units="", width=520, height=220):
    if not values:
        return ""
    vmax = max(values) or 1.0
    n = len(values)
    bw = (width - 60) / n
    bars = []
    for i, (lab, v) in enumerate(zip(labels, values)):
        h = (v / vmax) * (height - 60)
        x = 50 + i * bw
        y = height - 30 - h
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw*0.7:.1f}" height="{h:.1f}" '
            f'fill="#3b6ea5"/>'
            f'<text x="{x+bw*0.35:.1f}" y="{height-15}" font-size="9" '
            f'text-anchor="middle">{html.escape(str(lab))}</text>'
            f'<text x="{x+bw*0.35:.1f}" y="{y-3:.1f}" font-size="9" '
            f'text-anchor="middle">{v:.3g}</text>'
        )
    return (
        f'<svg width="{width}" height="{height}" '
        f'style="font-family:sans-serif">'
        f'<text x="{width/2}" y="16" text-anchor="middle" '
        f'font-size="12" font-weight="bold">{html.escape(title)} '
        f'[{html.escape(units)}]</text>' + "".join(bars) + "</svg>"
    )


def _shmoo_html(sh):
    if not sh["x"] or not sh["y"]:
        return "<p>No shmoo data.</p>"
    rows = ["<table class='shmoo'><tr><th></th>" +
            "".join(f"<th>{x:g}</th>" for x in sh["x"]) + "</tr>"]
    for y in sh["y"]:
        cells = [f"<th>{y:g}</th>"]
        for x in sh["x"]:
            frac = sh["grid"].get((y, x))
            if frac is None:
                cells.append("<td class='na'>-</td>")
            elif frac >= 0.999:
                cells.append("<td class='pass'>P</td>")
            elif frac <= 0.001:
                cells.append("<td class='fail'>F</td>")
            else:
                cells.append(f"<td class='part'>{frac*100:.0f}%</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    rows.append("</table>")
    cap = f"<p class='cap'>rows = {sh['y_key']}, cols = {sh['x_key']}</p>"
    return "".join(rows) + cap


CSS = """
body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:40px;color:#1a1a1a;max-width:900px}
h1{border-bottom:3px solid #3b6ea5;padding-bottom:6px}
h2{color:#3b6ea5;margin-top:32px}
table{border-collapse:collapse;margin:12px 0;font-size:14px}
th,td{border:1px solid #ccc;padding:6px 10px;text-align:center}
th{background:#f0f4f8}
.pass{background:#cdebcd}.fail{background:#f3c6c6}.part{background:#f6e7b0}.na{color:#aaa}
.banner{background:#fff8e1;border:1px solid #e0c060;padding:10px 14px;border-radius:6px;font-size:13px}
.cap{color:#666;font-size:12px}
.summary{font-size:15px}
.ok{color:#1a7a1a;font-weight:bold}.bad{color:#a11;font-weight:bold}
"""


def render_html(rows, dut, data_source_note: str) -> str:
    params = sorted({r["parameter"] for r in rows})
    total = len(rows)
    passed = sum(1 for r in rows if r["passed"])
    overall_yield = (100.0 * passed / total) if total else 0.0

    # per-parameter spec table
    spec_rows = []
    for p in params:
        s = analysis.summarize_parameter(rows, p)
        d = s["dist"]
        cpk_v = s["cpk"]
        cpk_txt = ("inf" if cpk_v == float("inf")
                   else (f"{cpk_v:.2f}" if cpk_v is not None else "n/a"))
        spec_rows.append(
            f"<tr><td>{html.escape(p)}</td>"
            f"<td>{s['lower'] if s['lower'] is not None else '-'}</td>"
            f"<td>{s['upper'] if s['upper'] is not None else '-'}</td>"
            f"<td>{d.get('mean',0):.4g}</td><td>{d.get('sigma',0):.3g}</td>"
            f"<td>{d.get('min',0):.4g}</td><td>{d.get('max',0):.4g}</td>"
            f"<td>{cpk_txt}</td>"
            f"<td class='{'pass' if s['yield_pct']>=99.9 else 'fail'}'>"
            f"{s['yield_pct']:.0f}%</td>"
            f"<td>{html.escape(s['units'])}</td></tr>"
        )
    spec_table = (
        "<table><tr><th>Parameter</th><th>LSL</th><th>USL</th><th>Mean</th>"
        "<th>Sigma</th><th>Min</th><th>Max</th><th>Cpk</th><th>Yield</th>"
        "<th>Units</th></tr>" + "".join(spec_rows) + "</table>"
    )

    # a shmoo for the first parameter that has 2D data
    shmoo_html = "<p>No 2D-swept parameter found.</p>"
    for p in params:
        sh = analysis.shmoo(rows, p)
        if sh["x"] and sh["y"]:
            shmoo_html = f"<h3>{html.escape(p)}</h3>" + _shmoo_html(sh)
            break

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    verdict = ("<span class='ok'>PASS</span>" if overall_yield >= 99.9
               else "<span class='bad'>REVIEW</span>")

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>PMU Validation Report - {html.escape(dut.part)}</title>
<style>{CSS}</style></head><body>
<h1>PMU Validation Report</h1>
<p class="summary"><b>DUT:</b> {html.escape(dut.part)} &mdash;
{html.escape(dut.description)}<br>
<b>Generated:</b> {ts}<br>
<b>Overall result:</b> {verdict} &nbsp; ({passed}/{total} measurements within
limits, {overall_yield:.1f}% yield)</p>
<div class="banner"><b>Data source:</b> {html.escape(data_source_note)}</div>
<h2>Spec Summary</h2>{spec_table}
<h2>Shmoo (pass/fail map)</h2>{shmoo_html}
<h2>Notes</h2>
<p class="cap">Part-to-part spread across multiple identical units is used as
the process-variation axis. Cpk and yield are computed over all logged
units and conditions.</p>
</body></html>"""


def write_report(rows, dut, out_path, data_source_note: str) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(rows, dut, data_source_note), encoding="utf-8")
    return out


def render_pdf(html_path, pdf_path) -> Path | None:
    """Convert HTML -> PDF if weasyprint is available; else skip gracefully."""
    try:
        from weasyprint import HTML
    except Exception:
        print("[report] weasyprint not installed; HTML only.")
        return None
    HTML(str(html_path)).write_pdf(str(pdf_path))
    return Path(pdf_path)
