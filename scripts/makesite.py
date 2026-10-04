"""Build the GitHub Pages site into docs/. Numbers come from the engine, not from hand typing."""
import html
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from medon import engine, web  # noqa: E402

REPO = "https://github.com/DIGlabUAB/medon"
LOGO = ('<svg viewBox="0 0 32 32" fill="none" stroke="#2456c8" stroke-width="1.8" stroke-linecap="round">'
        '<path d="M6 8h20M9 11h14M11.5 11v14M16 11v14M20.5 11v14M7 26h18"/></svg>')


def main():
    data = engine.load_all()
    org = yaml.safe_load((ROOT / "src/medon/data/org.example.yaml").read_text())
    qs = data["questionnaire"]["questions"]
    n_qb = sum(1 for q in qs if q["type"] == "status")
    controls = data["sources"]["controls"]
    fws = ""
    for fid, f in data["sources"]["frameworks"].items():
        n = sum(1 for c in controls if c.get("framework") == fid)
        fws += f'<li><a href="{f["url"]}">{html.escape(f["name"])}</a><span>{n} controls</span></li>'
    page = (ROOT / "site/template.html").read_text()
    rep = {"LOGO": LOGO, "REPO": REPO, "VERSION": "0.1.0", "FWS": fws,
           "N_CONTROLS": str(len(controls)), "N_FW": str(len(data["sources"]["frameworks"])),
           "N_QA": str(len(qs) - n_qb), "N_QB": str(n_qb)}
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
