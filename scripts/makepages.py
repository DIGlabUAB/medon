"""Build the scenario gallery, 100 sample reports and the sources page into docs/."""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenarios as S  # noqa: E402
from medon import engine, render  # noqa: E402

ROOT = S.ROOT
DOCS = ROOT / "docs"
REPO = "https://github.com/DIGlabUAB/medon"
e = html.escape
LOGO = ('<svg viewBox="0 0 32 32" fill="none" stroke="#2456c8" stroke-width="1.8" stroke-linecap="round">'
        '<path d="M6 8h20M9 11h14M11.5 11v14M16 11v14M20.5 11v14M7 26h18"/></svg>')
CSS = """:root{--bg:#fff;--soft:#f7f8fa;--fg:#16191d;--mut:#5d6570;--line:#e7e9ec;--ac:#2456c8;
--sans:'Inter',ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif;--mono:'JetBrains Mono',ui-monospace,Menlo,monospace;--hi:#c2462b;--mo:#c98a12;--lo:#2c8a6e}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
a{color:var(--ac);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1040px;margin:0 auto;padding:0 24px}
nav{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
nav .wrap{display:flex;align-items:center;justify-content:space-between;height:60px}.brand{display:flex;gap:9px;align-items:center;font-weight:600;color:var(--fg)}.brand:hover{text-decoration:none}.brand svg{width:22px;height:22px}
.nl{display:flex;gap:28px;align-items:center}.nl a{color:var(--mut);font-size:15px}.nl a:hover{color:var(--fg);text-decoration:none}
.btn{display:inline-block;padding:8px 14px;border-radius:8px;border:1px solid var(--line);font:500 14px var(--sans);cursor:pointer;background:#fff;color:var(--fg)}.btn:hover{text-decoration:none;border-color:#c9ced5}
h1{font-weight:600;font-size:clamp(32px,4.4vw,44px);letter-spacing:-.025em;line-height:1.12;margin:0 0 14px}
.lede{max-width:640px;color:var(--mut);font-size:18px;margin:0 0 40px}.page{padding:72px 0 96px}
.tag{display:inline-block;padding:2px 10px;border-radius:999px;font:500 12px var(--sans);text-transform:capitalize;color:#fff}
.tag.high{background:var(--hi)}.tag.moderate{background:var(--mo)}.tag.low{background:var(--lo)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}
.sc{border:1px solid var(--line);background:#fff;border-radius:10px;padding:16px 18px;cursor:pointer;text-align:left;color:inherit;font:inherit;transition:border-color .15s}
.sc:hover,.sc[aria-pressed=true]{border-color:var(--ac)}.sc h3{margin:10px 0 4px;font-weight:600;font-size:16px;line-height:1.3}.sc p{margin:0;color:var(--mut);font-size:14px}
.sc .n{margin-top:10px;color:var(--mut);font-size:14px}.sc .n b{color:var(--fg);font-weight:600}
.viewer{margin-top:36px;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#fff}
.vbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;background:var(--soft);border-bottom:1px solid var(--line);padding:12px 16px}.vbar .vt{font-weight:600;margin-right:8px}
.mt[aria-pressed=true]{background:var(--ac);border-color:var(--ac);color:#fff}
iframe{display:block;width:100%;height:760px;border:0;background:#fff}
table{width:100%;border-collapse:collapse;font-size:15px}th{font:500 13px var(--sans);text-align:left;color:var(--mut);padding:10px 12px;border-bottom:1px solid var(--line)}
td{padding:12px;border-bottom:1px solid var(--line);vertical-align:top}td.id{font:13px var(--mono);color:var(--mut);white-space:nowrap}
.fwh{margin:56px 0 12px}.fwh h2{margin:0 0 6px;font-weight:600;font-size:22px;letter-spacing:-.01em}.fwh p{margin:2px 0;color:var(--mut);font-size:14px}
input[type=search]{background:#fff;border:1px solid var(--line);color:var(--fg);padding:11px 14px;border-radius:8px;width:min(420px,100%);font:inherit}
input[type=search]:focus{outline:2px solid var(--ac);outline-offset:-1px}
.st{font-size:12px;color:var(--mut);border:1px solid var(--line);padding:1px 8px;border-radius:999px}
.note{margin-top:40px;color:var(--mut);font-size:14px}
@media(max-width:800px){.nl a.x{display:none}iframe{height:640px}td:nth-child(4),th:nth-child(4){display:none}}"""
HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>{t}</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">'
        '<style>' + CSS + '</style></head><body>')
NAV = ('<nav><div class="wrap"><a class="brand" href="../index.html">' + LOGO + 'Medon</a><div class="nl">'
       '<a class="x" href="../index.html#how">How it works</a><a class="x" href="../scenarios/index.html">Examples</a><a class="x" href="../sources/index.html">Sources</a>'
       '<a class="x" href="../app/index.html">Planner</a><a href="' + REPO + '">GitHub</a></div></div></nav>')


def slug(i, lv):
    return f"s{i+1:02d}m{lv}"


def build_scenarios(data):
    out = DOCS / "scenarios"
    (out / "reports").mkdir(parents=True, exist_ok=True)
    cards, meta = "", []
    for ai, (name, exp, ans) in enumerate(S.A):
        for lv in range(5):
            a = {**ans, **S.maturity(lv)}
            p = engine.build_plan(a, None, None, data)
            proj = {"name": f"{name} (scenario {slug(ai, lv)}, governance level {S.MAT[lv]})", "date": "synthetic scenario"}
            (out / "reports" / f"{slug(ai, lv)}.html").write_text(render.render_html(p, proj, None, data), encoding="utf-8")
            if lv == 2:
                why = "; ".join(p["tier_why"][:2]) or "no tier drivers"
                cards += (f'<button class="sc" data-i="{ai}" aria-pressed="false"><span class="tag {p["tier"]}">{p["tier"]}</span>'
                          f'<h3>{e(name)}</h3><p>{e(why)}</p><div class="n"><b>{p["total"]}</b> checklist items</div></button>')
    page = HEAD.replace("{t}", "Medon scenarios") + NAV + f"""<main class="page"><div class="wrap">
<h1>Example plans</h1>
<p class="lede">Twenty made-up projects, from a clinic no-show model to an insulin dosing system. Pick one, then choose how much governance is already in place, to see the plan Medon writes.</p>
<div class="grid" id="g">{cards}</div>
<div class="viewer" id="v" hidden><div class="vbar"><span class="vt" id="vt"></span>
<button class="btn mt" data-l="0">None</button><button class="btn mt" data-l="1">Owner and committee</button><button class="btn mt" data-l="2">Partial</button><button class="btn mt" data-l="3">Strong</button><button class="btn mt" data-l="4">Full</button>
<a class="btn" id="vo" href="#" target="_blank" style="margin-left:auto">Open report</a></div>
<iframe id="f" title="Scenario report"></iframe></div>
<p class="note">Scenario definitions and results: <a href="{REPO}/blob/main/scripts/scenarios.py">scenarios.py</a> and <a href="{REPO}/blob/main/results/scenarios.csv">scenarios.csv</a>.</p>
</div></main>
<script>
var cur=0,lv=2,names=@@NAMES@@;
function show(){{var s='reports/s'+String(cur+1).padStart(2,'0')+'m'+lv+'.html';document.getElementById('f').src=s;document.getElementById('vo').href=s;
document.getElementById('vt').textContent=names[cur];
document.querySelectorAll('.mt').forEach(function(b){{b.setAttribute('aria-pressed',String(+b.dataset.l===lv))}});
document.querySelectorAll('.sc').forEach(function(b){{b.setAttribute('aria-pressed',String(+b.dataset.i===cur))}});}}
document.querySelectorAll('.sc').forEach(function(b){{b.onclick=function(){{cur=+b.dataset.i;document.getElementById('v').hidden=false;show();document.getElementById('v').scrollIntoView({{behavior:'smooth'}})}}}});
document.querySelectorAll('.mt').forEach(function(b){{b.onclick=function(){{lv=+b.dataset.l;show()}}}});
</script></body></html>""".replace("@@NAMES@@", json.dumps([n for n, _, _ in S.A]))
    (out / "index.html").write_text(page, encoding="utf-8")


def build_sources(data):
    out = DOCS / "sources"
    out.mkdir(parents=True, exist_ok=True)
    used = {}
    for it in data["items"]["items"]:
        for c in it["sources"]:
            used.setdefault(c, []).append(it["id"])
    body = ""
    for fid, f in data["sources"]["frameworks"].items():
        rows = ""
        for c in data["sources"]["controls"]:
            if c["framework"] != fid:
                continue
            rows += (f'<tr><td class="id">{c["id"]}</td><td>{e(c["clause"])}</td><td>{e(c["requirement"])}</td>'
                     f'<td class="id">{", ".join(used.get(c["id"], [])) or "none"}</td><td><span class="st">{e(c["status"])}</span></td></tr>')
        body += (f'<div class="fwh"><h2>{e(f["name"])}</h2>'
                 f'<p>{e(f["cite"])} <a href="{f["url"]}">Source document</a></p></div>'
                 f'<table class="ct"><thead><tr><th>Control</th><th>Clause</th><th>Requirement (paraphrase)</th><th>Plan items</th><th>Review</th></tr></thead><tbody>{rows}</tbody></table>')
    n = len(data["sources"]["controls"])
    page = HEAD.replace("{t}", "Medon sources") + NAV + f"""<main class="page"><div class="wrap">
<h1>Sources</h1>
<p class="lede">{n} controls from {len(data["sources"]["frameworks"])} published frameworks. Each checklist item cites the controls below. Requirements are short paraphrases; always check the source document.</p>
<input type="search" id="q" placeholder="Filter by clause or keyword">{body}
<p class="note">Planned: NIST AI 600-1 generative AI profile, CHAI Assurance Reporting Checklists, FDA clinical decision support guidance, HIPAA security rule and state AI laws. <a href="{REPO}/blob/main/CONTRIBUTING.md">Add a framework.</a></p>
</div></main>
<script>document.getElementById('q').oninput=function(){{var v=this.value.toLowerCase();document.querySelectorAll('.ct tbody tr').forEach(function(r){{r.style.display=r.textContent.toLowerCase().indexOf(v)<0?'none':''}})}}</script>
</body></html>"""
    (out / "index.html").write_text(page, encoding="utf-8")


def main():
    data = engine.load_all()
    build_scenarios(data)
    build_sources(data)
    print("pages written")


if __name__ == "__main__":
    main()
