import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_scenarios_reproduce_locked_results():
    f = ROOT / "results" / "scenarios.json"
    before = json.loads(f.read_text())
    subprocess.run([sys.executable, str(ROOT / "scripts" / "scenarios.py")], check=True, cwd=ROOT, capture_output=True)
    after = json.loads(f.read_text())
    assert before == after
    assert after["n_scenarios"] == 100
    assert after["tier_counts_archetypes"] == {"high": 9, "moderate": 6, "low": 5}
    assert len(after["discordant"]) == 2
