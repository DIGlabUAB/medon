"""Build the GitHub Pages site into docs/. Numbers come from the engine, not from hand typing."""
import html
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import art  # noqa: E402
from medon import engine, render, web  # noqa: E402

REPO = "https://github.com/DIGlabUAB/medon"
LOGO = ('<svg viewBox="0 0 32 32" fill="none" stroke="#c4501a" stroke-width="1.8" stroke-linecap="round">'
        '<path d="M6 8h20M9 11h14M11.5 11v14M16 11v14M20.5 11v14M7 26h18"/></svg>')


def hl_yaml(text):
    out = []
    for line in text.splitlines():
        e = html.escape(line)
        if e.strip().startswith("#"):
            out.append(f'<span class="c">{e}</span>')
            continue
        m = re.match(r"^(\s*)([A-Za-z_]+)(:)(.*)$", e)
        out.append(f'{m.group(1)}<span class="k">{m.group(2)}</span>{m.group(3)}<span class="v">{m.group(4)}</span>' if m else e)
    return "\n".join(out)


def main():
    data = engine.load_all()
    org = yaml.safe_load((ROOT / "src/medon/data/org.example.yaml").read_text())
    qs = data["questionnaire"]["questions"]
    n_qb = sum(1 for q in qs if q["type"] == "status")
    sep = yaml.safe_load((ROOT / "examples/sepsis.yaml").read_text())
    plan = engine.build_plan(sep["answers"], org, None, data)
    md_lines = render.render_md(plan, sep["project"], org, data).splitlines()
    start = next(i for i, l in enumerate(md_lines) if l.startswith("## Before deployment"))
    excerpt = "\n".join(md_lines[:7] + [""] + md_lines[start:start + 12] + ["", "..."])
    ans_txt = "\n".join(l for l in (ROOT / "examples/sepsis.yaml").read_text().splitlines())
    org_txt = (ROOT / "src/medon/data/org.example.yaml").read_text()
    tiers = ""
    for name, f, blurb in (("low", "scheduling", "Administrative tools. Short list, light touch."),
                           ("moderate", "scribe", "Clinical information tools. Patient transparency, local validation, bias audit."),
                           ("high", "sepsis", "Close to a clinical decision. Suspension criteria, oversight, external reporting.")):
        d = yaml.safe_load((ROOT / f"examples/{f}.yaml").read_text())
        p = engine.build_plan(d["answers"], None, None, data)
        total = len(data["items"]["items"])
        bars = "".join(f'<i class="{"f" if k < p["total"] else ""}"></i>' for k in range(total))
        tiers += (f'<div class="tier reveal"><div class="mono" style="opacity:.6">{name} tier</div>'
                  f'<div class="n">{p["total"]}</div><h4>items in the plan</h4><p>{blurb}</p><div class="bars">{bars}</div></div>')
    fws = ""
    for fid, f in data["sources"]["frameworks"].items():
        n = sum(1 for c in data["sources"]["controls"] if c.get("framework") == fid) if isinstance(data["sources"]["controls"], list) else sum(1 for c in data["sources"]["controls"].values() if c.get("framework") == fid)
        fws += (f'<div class="fw reveal"><div class="mono" style="opacity:.6">Encoded &middot; {f["date"]}</div><div class="n">{n}</div>'
                f'<h4>{html.escape(f["name"])}</h4><p>controls mapped to plan items.</p><a href="{f["url"]}">Source document</a></div>')
    road = "".join(f"<span>{x}</span>" for x in ("NIST AI 600-1 generative AI profile", "CHAI Assurance Reporting Checklists", "FDA clinical decision support guidance", "HIPAA security rule", "State AI laws", "Your institution policies"))
    marq = "".join(f'<span class="wm"><i></i>{html.escape(f["short"])}</span>' for f in data["sources"]["frameworks"].values())
    marq += "".join(f'<span class="wm pl"><i></i>{x}</span>' for x in ("NIST AI 600-1 generative AI profile", "CHAI Assurance Reporting Checklists", "FDA clinical decision support guidance", "HIPAA security rule", "State AI laws"))
    import scenarios as SC
    scen = ""
    for ai in (3, 0, 6):
        nm, _, ans = SC.A[ai]
        p2 = engine.build_plan({**ans, **SC.maturity(2)}, None, None, data)
        scen += (f'<a class="card reveal" href="scenarios/reports/s{ai+1:02d}m2.html" style="text-decoration:none"><div class="t"><span class="mono" style="color:var(--cu)">{p2["tier"]} tier</span>'
                 f'<h3>{html.escape(nm)}</h3><p>{p2["total"]} items. {p2["counts"]["done"]} done, {p2["counts"]["in progress"]} in progress, {p2["counts"]["open"]} open.</p></div>'
                 f'<div class="art"><span class="chip on">Open the report</span></div></a>')
    page = (ROOT / "site/template.html").read_text()
    rep = {"LOGO": LOGO, "REPO": REPO, "VERSION": "0.1.0", "ARCH": art.arch(), "SEAL": art.seal(),
           "N_CONTROLS": str(len(data["sources"]["controls"])), "N_FW": str(len(data["sources"]["frameworks"])),
           "N_ITEMS": str(len(data["items"]["items"])), "N_Q": str(len(qs)), "N_QA": str(len(qs) - n_qb), "N_QB": str(n_qb),
           "CODE_ANSWERS": hl_yaml(ans_txt), "CODE_PLAN": html.escape(excerpt),
           "CODE_ORG": hl_yaml(org_txt), "TIERS": tiers, "FWS": fws, "ROAD": road, "MARQ": marq, "CORNER": art.corner(), "COLUMN": art.column(), "SCEN": scen}
    for k, v in rep.items():
        page = page.replace("{{" + k + "}}", v)
    assert "{{" not in page
    docs = ROOT / "docs"
    (docs / "app").mkdir(parents=True, exist_ok=True)
    (docs / "index.html").write_text(page, encoding="utf-8")
    (docs / "app" / "index.html").write_text(web.build_page(org), encoding="utf-8")
    (docs / ".nojekyll").write_text("")
    import makepages
    makepages.main()
    print("site written")


if __name__ == "__main__":
    main()
