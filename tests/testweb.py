"""The web engine must give the same plan as the Python engine."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from medon import engine, web

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
ROOT = Path(__file__).resolve().parent.parent
CASES = [yaml.safe_load(open(p))["answers"] for p in sorted((ROOT / "examples").glob("*.yaml"))] + [
    {}, {"function": "diagnostic", "harm": "unsure", "users": ["patients", "clinicians"], "x_owner": "partial"},
]
ORG = {"roles": {"governance_lead": "CMIO"}, "cadence": {"monitoring": {"high": "monthly", "moderate": "q", "low": "a"}}}
JS = """
const fs=require('fs');const E=require(process.argv[2]);
const d=JSON.parse(fs.readFileSync(0,'utf8'));
console.log(JSON.stringify(d.cases.map(c=>E.build(d.data,c.a,d.org,c.o))));
"""


def test_parity(tmp_path):
    data = engine.load_all()
    data["disclaimer"] = ""
    cases = [{"a": a, "o": o} for a in CASES for o in (None, "high")]
    py = [engine.build_plan(c["a"], ORG, c["o"], data) for c in cases]
    js_file = tmp_path / "run.js"
    js_file.write_text(JS)
    eng = str(ROOT / "src/medon/data/web/engine.js")
    out = subprocess.run(["node", str(js_file), eng], input=json.dumps({"data": data, "cases": cases, "org": ORG}),
                         capture_output=True, text=True, check=True).stdout
    js = json.loads(out)
    norm = lambda x: json.loads(json.dumps(x))
    for p, j in zip(py, js):
        assert norm(p) == j


def test_page_is_self_contained():
    page = web.build_page({"organization": "Test Org"})
    assert "Test Org" in page
    assert "http://" not in page.replace("http://www.w3.org", "") and "https://" not in page.split("MEDON_DATA")[0]
    for tag in ("<link", "src=\"http"):
        assert tag not in page
