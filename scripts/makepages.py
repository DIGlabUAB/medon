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
LOGO = ('<svg viewBox="0 0 32 32" fill="none" stroke="#e4672a" stroke-width="1.6" stroke-linecap="round">'
        '<path d="M6 8h20M9 11h14M11.5 11v14M16 11v14M20.5 11v14M7 26h18"/></svg>')
CSS = """:root{--navbg:rgba(19,20,21,.9);--ink:#131415;--ink2:#1c1d20;--paper:#ddd5c8;--paper3:#f4f0e9;--cu:#e4672a;--line:rgba(221,213,200,.16);--pline:rgba(19,20,21,.14);
--sans:'Inter Tight',ui-sans-serif,system-ui,sans-serif;--mono:'JetBrains Mono',ui-monospace,Menlo,monospace;--hi:#c4501a;--mo:#d6a21c;--lo:#2e8f7a}
*{box-sizing:border-box}body{margin:0;background:var(--ink);color:var(--paper);font:16px/1.55 var(--sans)}a{color:inherit}
.wrap{max-width:1180px;margin:0 auto;padding:0 28px}.mono{font:12px var(--mono);text-transform:uppercase;letter-spacing:.14em}
nav{position:sticky;top:0;z-index:20;background:var(--navbg);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
nav .wrap{display:flex;align-items:center;justify-content:space-between;height:60px}.brand{display:flex;gap:10px;align-items:center;font-weight:600;text-decoration:none}.brand svg{width:22px;height:22px}
.nl{display:flex;gap:24px;align-items:center}.nl a{text-decoration:none;opacity:.8;font-size:14px}.nl a:hover{opacity:1}
.btn{display:inline-block;padding:10px 18px;border-radius:999px;border:1px solid var(--line);text-decoration:none;font-size:14px;cursor:pointer;background:none;color:var(--paper);font-family:var(--sans)}
.btn.p{background:var(--cu);color:#151515;border-color:var(--cu)}h1{font-weight:500;font-size:clamp(34px,5vw,56px);letter-spacing:-.03em;line-height:1.05;margin:14px 0 14px}
.lede{max-width:640px;opacity:.8;font-size:18px;margin:0 0 36px}.page{padding:70px 0 90px}
.tag{display:inline-block;padding:3px 10px;border-radius:999px;font:11px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:#151515}
.tag.high{background:var(--hi);color:#fff}.tag.moderate{background:var(--mo)}.tag.low{background:var(--lo);color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}
.sc{border:1px solid var(--line);background:var(--ink2);border-radius:14px;padding:18px;cursor:pointer;text-align:left;color:inherit;font:inherit;transition:border-color .2s,transform .2s}
.sc:hover,.sc[aria-pressed=true]{border-color:var(--cu);transform:translateY(-2px)}.sc h3{margin:10px 0 6px;font-weight:500;font-size:18px;line-height:1.25}.sc p{margin:0;opacity:.65;font-size:13.5px}
.sc .n{font:500 30px/1 var(--sans);color:var(--cu);margin-top:12px;letter-spacing:-.03em}
.viewer{margin-top:36px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff}
.vbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;background:#26282c;padding:12px 16px}.vbar .mono{opacity:.7;margin-right:8px}
.mt{padding:6px 12px;font-size:13px}.mt[aria-pressed=true]{background:var(--paper);color:var(--ink)}
iframe{display:block;width:100%;height:760px;border:0;background:#fff}
table{width:100%;border-collapse:collapse;font-size:14.5px}th{font:11px var(--mono);text-transform:uppercase;letter-spacing:.12em;text-align:left;opacity:.6;padding:10px 12px;border-bottom:1px solid var(--line)}
td{padding:12px;border-bottom:1px solid var(--line);vertical-align:top}td.id{font-family:var(--mono);color:var(--cu);white-space:nowrap}
.fwh{border:1px solid var(--line);border-radius:14px;padding:22px;background:var(--ink2);margin:30px 0 8px}.fwh h2{margin:0 0 6px;font-weight:500;font-size:24px}.fwh p{margin:4px 0;opacity:.75;font-size:14px}
input[type=search]{background:var(--ink2);border:1px solid var(--line);color:var(--paper);padding:12px 16px;border-radius:999px;width:min(420px,100%);font:inherit;margin-bottom:10px}
.st{font:11px var(--mono);text-transform:uppercase;letter-spacing:.1em;border:1px dashed var(--line);padding:2px 8px;border-radius:999px;opacity:.8}
html[data-theme=light]{--ink:#f5f1e9;--ink2:#ebe5d9;--paper:#17181a;--line:rgba(19,20,21,.16);--navbg:rgba(245,241,233,.86)}
.tg{width:38px;height:38px;border-radius:50%;border:1px solid var(--line);background:none;color:var(--paper);cursor:pointer;padding:0;font-size:16px}
@media(max-width:800px){.nl a:not(.btn){display:none}iframe{height:640px}td:nth-child(4){display:none}th:nth-child(4){display:none}}"""
HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>{t}</title><link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
        '<style>' + CSS + '</style></head><body>')
NAV = ('<nav><div class="wrap"><a class="brand" href="../index.html">' + LOGO + 'Medon</a><div class="nl">'
       '<a href="../index.html#how">How it works</a><a href="../scenarios/index.html">Scenarios</a><a href="../sources/index.html">Sources</a>'
       '<a href="../app/index.html">Planner</a><a class="btn sm" href="' + REPO + '">GitHub</a><button class="tg" id="tg" aria-label="Light or dark background">&#9680;</button></div></div></nav>')


THEME = """<script>(function(){var r=document.documentElement,k='gp-theme';function g(){try{var v=localStorage.getItem(k);if(v)return v}catch(e){}return window.matchMedia&&matchMedia('(prefers-color-scheme: light)').matches?'light':'dark'}
r.setAttribute('data-theme',g());document.getElementById('tg').onclick=function(){var v=r.getAttribute('data-theme')==='light'?'dark':'light';r.setAttribute('data-theme',v);try{localStorage.setItem(k,v)}catch(e){}}})();</script>"""


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
                          f'<h3>{e(name)}</h3><p>{e(why)}</p><div class="n">{p["total"]}<span class="mono" style="font-size:11px;opacity:.6"> &nbsp;items</span></div></button>')
    page = HEAD.replace("{t}", "Medon scenarios") + NAV + f"""<main class="page"><div class="wrap">
<div class="mono" style="color:var(--cu)">Scenarios</div><h1>20 projects. 100 plans.</h1>
<p class="lede">Pick a project type, then a level of existing governance. The report is the plan Medon writes for that project, with owners, evidence and source clauses. Every scenario is synthetic.</p>
<div class="grid" id="g">{cards}</div>
<div class="viewer" id="v" hidden><div class="vbar"><span class="mono" id="vt"></span>
<button class="btn mt" data-l="0">None</button><button class="btn mt" data-l="1">Owner and committee</button><button class="btn mt" data-l="2">Partial</button><button class="btn mt" data-l="3">Strong</button><button class="btn mt" data-l="4">Full</button>
<a class="btn" id="vo" href="#" target="_blank" style="margin-left:auto">Open report</a></div>
<iframe id="f" title="Scenario report"></iframe></div>
<p style="margin-top:30px;opacity:.7;font-size:14px">Scenario definitions and results: <a href="{REPO}/blob/main/scripts/scenarios.py">scenarios.py</a> and <a href="{REPO}/blob/main/results/scenarios.csv">scenarios.csv</a>.</p>
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
        body += (f'<div class="fwh"><div class="mono" style="color:var(--cu)">{e(f["short"])} &middot; {e(f["date"])}</div><h2>{e(f["name"])}</h2>'
                 f'<p>{e(f["cite"])}</p><p><a href="{f["url"]}">Open the source document</a></p></div>'
                 f'<table class="ct"><thead><tr><th>Control</th><th>Clause</th><th>Requirement (paraphrase)</th><th>Plan items</th><th>Review</th></tr></thead><tbody>{rows}</tbody></table>')
    n = len(data["sources"]["controls"])
    page = HEAD.replace("{t}", "Medon sources") + NAV + f"""<main class="page"><div class="wrap">
<div class="mono" style="color:var(--cu)">Sources</div><h1>{n} controls from {len(data["sources"]["frameworks"])} frameworks.</h1>
<p class="lede">Each plan item cites the controls below. Requirements are one sentence paraphrases. The review column shows where each mapping stands, so reviewers can see what has been checked against the source.</p>
<input type="search" id="q" placeholder="Filter by clause or keyword">{body}
<div class="mono" style="margin:48px 0 12px;opacity:.6">Planned</div>
<p style="opacity:.8">NIST AI 600-1 generative AI profile, CHAI Assurance Reporting Checklists, FDA clinical decision support guidance, HIPAA security rule and state AI laws. <a href="{REPO}/blob/main/CONTRIBUTING.md" style="color:var(--cu)">Add a framework.</a></p>
</div></main>
<script>document.getElementById('q').oninput=function(){{var v=this.value.toLowerCase();document.querySelectorAll('.ct tbody tr').forEach(function(r){{r.style.display=r.textContent.toLowerCase().indexOf(v)<0?'none':''}})}}</script>
</body></html>""".replace("</body>", THEME + "</body>")
    (out / "index.html").write_text(page, encoding="utf-8")


def main():
    data = engine.load_all()
    build_scenarios(data)
    build_sources(data)
    print("pages written")


if __name__ == "__main__":
    main()
