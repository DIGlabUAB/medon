"""Render a plan as markdown, html, json or csv."""
from __future__ import annotations

import csv
import html
import io
import json

from .engine import load_all

DISCLAIMER = ("This plan maps your answers to requirements in published governance documents. "
              "Medon is a planning aid that supports your governance committee and counsel. "
              "Each mapping to a source document carries a review status.")
MARK = {"done": "[x]", "in progress": "[~]", "open": "[ ]"}


def _phases(data):
    return data["items"]["phases"]


def _src(s):
    return f"{s['framework']} {s['clause']} ({s['id']})"


def _freq(i):
    if not i["frequency_needed"]:
        return None
    return i["frequency"] or "Set by local policy"


def _refs(plan, data):
    used = {s["framework"] for i in plan["items"] for s in i["sources"]}
    fw = data["sources"]["frameworks"]
    return [f["cite"] for k, f in fw.items() if k in used or f["short"] in used or f["name"] in used]


def render_md(plan, project=None, org=None, data=None):
    data = data or load_all()
    project = project or {}
    org = org or {}
    L = [f"# Governance plan: {project.get('name') or 'Unnamed project'}", ""]
    meta = [("Organization", org.get("organization")), ("Clinical lead", project.get("clinical_lead")),
            ("Date", project.get("date"))]
    L += [f"- {k}: {v}" for k, v in meta if v]
    t = plan["tier"]
    L.append(f"- Risk tier: **{t}**" + (" (set by override)" if plan["tier_overridden"] else ""))
    if plan["tier_why"] and not plan["tier_overridden"]:
        L.append("- Tier reasons: " + "; ".join(plan["tier_why"]))
    if plan["tier_overridden"]:
        L.append(f"- Computed tier was {plan['tier_computed']}. Override reason: {project.get('tier_override_reason') or 'not given'}")
    c = plan["counts"]
    L.append(f"- Items: {plan['total']} ({c['done']} done, {c['in progress']} in progress, {c['open']} open)")
    if plan["unanswered"]:
        L.append("- Unanswered questions, treated as unsure: " + ", ".join(plan["unanswered"]))
    L += ["", DISCLAIMER, ""]
    for ph in _phases(data):
        its = [i for i in plan["items"] if i["phase"] == ph["id"]]
        if not its:
            continue
        L += [f"## {ph['title']}", ""]
        for i in its:
            flag = " Confirm: depends on an unsure answer." if i["confirm"] else ""
            L.append(f"- {MARK[i['status']]} **{i['id']} {i['title']}** ({i['status']}){flag}")
            L.append(f"  - Do: {i['action']}")
            L.append(f"  - Evidence: {i['evidence']}")
            own = i["owner"] or f"Set by local policy (role: {i['owner_role'].replace('_', ' ')})"
            L.append(f"  - Owner: {own}")
            f = _freq(i)
            if f:
                L.append(f"  - Frequency: {f}")
            if i["local_policy"]:
                L.append(f"  - Local policy: {i['local_policy']}")
            if i["sources"]:
                L.append("  - Source: " + "; ".join(_src(s) for s in i["sources"]))
            else:
                L.append("  - Source: none. Local consideration, not required by an encoded document.")
        L.append("")
    L.append("## References")
    L.append("")
    L += [f"{n}. {c}" for n, c in enumerate(_refs(plan, data), 1)]
    L.append("")
    return "\n".join(L)


def render_json(plan, project=None, org=None, data=None):
    return json.dumps({"project": project or {}, "organization": (org or {}).get("organization"),
                       "plan": plan, "disclaimer": DISCLAIMER}, indent=2, default=str)


def render_csv(plan, project=None, org=None, data=None):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "phase", "item", "status", "owner", "frequency", "evidence", "sources", "confirm"])
    for i in plan["items"]:
        w.writerow([i["id"], i["phase"], i["title"], i["status"],
                    i["owner"] or "Set by local policy", _freq(i) or "", i["evidence"],
                    "; ".join(_src(s) for s in i["sources"]) or "none", "yes" if i["confirm"] else ""])
    return buf.getvalue()


CSS = """:root{--bg:#fff;--card:#fff;--fg:#16191d;--mut:#5d6570;--line:#e3e6ea;--cu:#2456c8;--lo:#2c8a6e;--mo:#c98a12;--hi:#c2462b;--done:#2c8a6e;--prog:#c98a12;--open:#c2462b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,'Segoe UI',sans-serif}
.pg{max-width:980px;margin:0 auto;padding:22px 18px 40px}.mono{font:11px ui-monospace,Menlo,Consolas,monospace;text-transform:uppercase;letter-spacing:.1em;color:var(--mut)}
h1{font-size:22px;margin:4px 0 6px;letter-spacing:-.01em}.top{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.tier{padding:3px 12px;border-radius:999px;color:#fff;font:600 12px ui-monospace,Menlo,monospace;text-transform:uppercase;letter-spacing:.1em}.tier.high{background:var(--hi)}.tier.moderate{background:var(--mo);color:#1a1a1a}.tier.low{background:var(--lo)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 0}.chip{border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:12px;color:var(--mut);background:var(--card)}
.viz{display:grid;grid-template-columns:1fr 1fr 1.2fr;gap:14px;margin:16px 0}.box{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}.box h3{margin:0 0 6px;font:11px ui-monospace,Menlo,monospace;text-transform:uppercase;letter-spacing:.1em;color:var(--mut);font-weight:500}
.box svg{display:block;width:100%;height:auto}.box .dn{max-width:170px;margin:0 auto}.lg{display:flex;gap:12px;justify-content:center;font-size:12px;color:var(--mut);margin-top:4px}.lg i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:4px}
.bar{display:grid;grid-template-columns:96px 1fr 34px;gap:8px;align-items:center;margin:7px 0;font-size:12px}.bar .t{display:flex;height:9px;border-radius:5px;overflow:hidden;background:var(--line)}.bar .t span{display:block;height:100%}.bar b{font-weight:500;text-align:right;color:var(--mut)}
.next{margin:0 0 14px}.next ol{margin:6px 0 0;padding-left:20px}.next li{margin:3px 0}
h2{font-size:13px;margin:22px 0 8px;display:flex;justify-content:space-between;font:500 12px ui-monospace,Menlo,monospace;text-transform:uppercase;letter-spacing:.1em;color:var(--mut);border-bottom:1px solid var(--line);padding-bottom:6px}
details.it{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:6px 0;break-inside:avoid}details.it summary{list-style:none;cursor:pointer;display:flex;gap:10px;align-items:center;padding:9px 12px}details.it summary::-webkit-details-marker{display:none}
.ck{width:18px;height:18px;border-radius:5px;border:1.6px solid var(--open);flex:none;display:grid;place-items:center;font-size:12px;color:#fff;line-height:1}.ck.done{background:var(--done);border-color:var(--done)}.ck.progress{border-color:var(--prog);background:linear-gradient(90deg,var(--prog) 50%,transparent 50%)}
.id{font:11px ui-monospace,Menlo,monospace;color:var(--cu);width:30px;flex:none}.tt{flex:1;font-weight:500;min-width:45%}.mt{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}.tg{font-size:11px;padding:1px 8px;border-radius:999px;border:1px solid var(--line);color:var(--mut);white-space:nowrap;max-width:150px;overflow:hidden;text-overflow:ellipsis}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:3px}.bd{padding:2px 14px 12px 50px;color:var(--mut);font-size:13px}.bd p{margin:4px 0}.bd b{color:var(--fg);font-weight:500}.bd ul{margin:4px 0 0;padding-left:16px}
.cf{color:var(--cu);font-size:12px}.note{color:var(--mut);font-size:12px;margin-top:22px;border-left:2px solid var(--cu);padding-left:10px}.refs{font-size:12px;color:var(--mut);padding-left:18px}
@media(max-width:760px){.viz{grid-template-columns:1fr}.mt{display:none}}
@media print{body{background:#fff;color:#000}details.it{break-inside:avoid}.pg{padding:0}}"""
FWCOL = ["#2b6cb0", "#c4501a", "#2e8f7a", "#8a5ab5", "#b8860b", "#c0398a", "#4a7a3a", "#607080"]
THEME_JS = ""


def _donut(c, total):
    import math
    r, cx = 46, 60
    circ = 2 * math.pi * r
    segs, off = [], 0.0
    for k, col in (("done", "var(--done)"), ("in progress", "var(--prog)"), ("open", "var(--open)")):
        ln = circ * c[k] / total if total else 0
        segs.append(f'<circle cx="{cx}" cy="{cx}" r="{r}" fill="none" stroke="{col}" stroke-width="14" stroke-dasharray="{ln:.2f} {circ - ln:.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {cx} {cx})"/>')
        off += ln
    pct = round(100 * c["done"] / total) if total else 0
    return (f'<svg class="dn" viewBox="0 0 120 120" role="img" aria-label="Status {c["done"]} done, {c["in progress"]} in progress, {c["open"]} open"><circle cx="{cx}" cy="{cx}" r="{r}" fill="none" stroke="var(--line)" stroke-width="14"/>'
            + "".join(segs) + f'<text x="{cx}" y="{cx + 2}" text-anchor="middle" font-size="22" font-weight="600" fill="currentColor">{pct}%</text><text x="{cx}" y="{cx + 16}" text-anchor="middle" font-size="8" fill="var(--mut)">DONE</text></svg>'
            '<div class="lg"><span><i style="background:var(--done)"></i>' + f'{c["done"]} done</span><span><i style="background:var(--prog)"></i>{c["in progress"]} in progress</span><span><i style="background:var(--open)"></i>{c["open"]} open</span></div>')


def _radar(prof, tier):
    import math
    R, n = 62, len(prof)
    col = {"high": "var(--hi)", "moderate": "var(--mo)", "low": "var(--lo)"}[tier]

    def pt(i, r):
        th = -math.pi / 2 + 2 * math.pi * i / n
        return r * math.cos(th), r * math.sin(th)
    g = "".join('<polygon fill="none" stroke="var(--line)" points="' + " ".join(f"{pt(i, R * k / 3)[0]:.1f},{pt(i, R * k / 3)[1]:.1f}" for i in range(n)) + '"/>' for k in (1, 2, 3))
    g += "".join(f'<line x1="0" y1="0" x2="{pt(i, R)[0]:.1f}" y2="{pt(i, R)[1]:.1f}" stroke="var(--line)"/>' for i in range(n))
    poly = " ".join(f"{pt(i, R * p['score'] / 3)[0]:.1f},{pt(i, R * p['score'] / 3)[1]:.1f}" for i, p in enumerate(prof))
    lab = ""
    for i, p in enumerate(prof):
        x, y = pt(i, R + 14)
        anc = "middle" if abs(x) < 6 else "start" if x > 0 else "end"
        lab += f'<text x="{x:.1f}" y="{y + 3:.1f}" text-anchor="{anc}" font-size="8.5" fill="var(--mut)">{html.escape(p["label"])}</text>'
    return (f'<svg viewBox="-150 -92 300 184" role="img" aria-label="Six axis risk profile">{g}<polygon points="{poly}" fill="{col}" fill-opacity=".25" stroke="{col}" stroke-width="1.6"/>{lab}</svg>')


def render_html(plan, project=None, org=None, data=None):
    data = data or load_all()
    project = project or {}
    org = org or {}
    e = html.escape
    items, c, total = plan["items"], plan["counts"], plan["total"]
    fws = data["sources"]["frameworks"]
    fcol = {f["short"]: FWCOL[k % len(FWCOL)] for k, f in enumerate(fws.values())}
    cover = {}
    for i in items:
        for fw in {s["framework"] for s in i["sources"]}:
            cover[fw] = cover.get(fw, 0) + 1
    meta = [x for x in (org.get("organization"), project.get("clinical_lead") and "Lead: " + project["clinical_lead"], project.get("date")) if x]
    out = [f"<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Governance plan</title><style>{CSS}</style>{THEME_JS}<body><div class='pg'>"]
    out.append("<div class='top'><span class='mono'>Governance plan</span>" + f"<span class='tier {plan['tier']}'>{e(plan['tier'])} tier</span>" + ("<span class='mono'>" + e(" / ".join(str(m) for m in meta)) + "</span>" if meta else "") + "</div>")
    out.append(f"<h1>{e(project.get('name') or 'Unnamed project')}</h1>")
    if plan["tier_why"] and not plan["tier_overridden"]:
        out.append("<div class='chips'>" + "".join(f"<span class='chip'>{e(w)}</span>" for w in plan["tier_why"]) + "</div>")
    # plots
    ph_rows = ""
    for ph in _phases(data):
        its = [i for i in items if i["phase"] == ph["id"]]
        if not its:
            continue
        n = len(its)
        seg = "".join(f'<span style="width:{100 * sum(1 for i in its if i["status"] == k) / n:.1f}%;background:var(--{v})"></span>' for k, v in (("done", "done"), ("in progress", "prog"), ("open", "open")))
        ph_rows += f'<div class="bar"><span>{e(ph["title"].split(" and ")[0])}</span><div class="t">{seg}</div><b>{n}</b></div>'
    fw_rows = "".join(f'<div class="bar"><span>{e(k)}</span><div class="t"><span style="width:{100 * v / total:.1f}%;background:{fcol.get(k, "#607080")}"></span></div><b>{v}</b></div>' for k, v in sorted(cover.items(), key=lambda kv: -kv[1]))
    out.append("<div class='viz'><div class='box'><h3>Status</h3>" + _donut(c, total) + "</div><div class='box'><h3>Risk profile</h3>" + _radar(plan["profile"], plan["tier"]) + "</div>"
               "<div class='box'><h3>Items by phase</h3>" + ph_rows + "<h3 style='margin-top:12px'>Items citing each framework</h3>" + fw_rows + "</div></div>")
    nxt = [i for i in items if i["status"] != "done"][:5]
    if nxt:
        out.append("<div class='box next'><h3>Start here</h3><ol>" + "".join(f"<li><span class='id' style='display:inline-block'>{e(i['id'])}</span>{e(i['title'])}</li>" for i in nxt) + "</ol></div>")
    for ph in _phases(data):
        its = [i for i in items if i["phase"] == ph["id"]]
        if not its:
            continue
        done = sum(1 for i in its if i["status"] == "done")
        out.append(f"<h2><span>{e(ph['title'])}</span><span>{done} of {len(its)} done</span></h2>")
        for i in its:
            cls = {"done": "done", "in progress": "progress", "open": "open"}[i["status"]]
            mark = "&#10003;" if cls == "done" else ""
            own = i["owner"] or i["owner_role"].replace("_", " ")
            f = _freq(i)
            tags = f"<span class='tg'>{e(own)}</span>" + (f"<span class='tg'>{e(f)}</span>" if f else "")
            fwset = []
            for sx in i["sources"]:
                if sx["framework"] not in fwset:
                    fwset.append(sx["framework"])
            dots = "".join(f"<span class='tg'><span class='dot' style='background:{fcol.get(k, '#607080')}'></span>{e(k)}</span>" for k in fwset[:3]) + (f"<span class='tg'>+{len(fwset) - 3}</span>" if len(fwset) > 3 else "")
            body = f"<p><b>Do</b> {e(i['action'])}</p><p><b>Evidence</b> {e(i['evidence'])}</p>"
            if i["local_policy"]:
                body += f"<p><b>Local policy</b> {e(i['local_policy'])}</p>"
            if i["confirm"]:
                body += "<p class='cf'>Confirm: depends on an unsure answer.</p>"
            body += "<p><b>Sources</b></p><ul>" + ("".join(f"<li>{e(sx['framework'])} {e(sx['clause'])} ({e(sx['id'])})</li>" for sx in i["sources"]) or "<li>Local consideration. No encoded clause.</li>") + "</ul>"
            out.append(f"<details class='it'><summary><span class='ck {cls}'>{mark}</span><span class='id'>{e(i['id'])}</span><span class='tt'>{e(i['title'])}</span><span class='mt'>{tags}{dots}</span></summary><div class='bd'>{body}</div></details>")
    out.append(f"<p class='note'>{e(DISCLAIMER)}</p>")
    out.append("<h2><span>References</span></h2><ol class='refs'>" + "".join(f"<li>{e(x)}</li>" for x in _refs(plan, data)) + "</ol></div></body></html>")
    return "\n".join(out)


RENDERERS = {"md": render_md, "html": render_html, "json": render_json, "csv": render_csv}
