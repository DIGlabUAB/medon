from pathlib import Path

import pytest

from medon import cli

EX = Path(__file__).resolve().parent.parent / "examples"
ORGF = Path(cli.__file__).parent / "data" / "org.example.yaml"


def run(*a):
    return cli.main(list(a))


def test_plan_formats(tmp_path, capsys):
    for fmt in ("md", "html", "json", "csv"):
        out = tmp_path / f"o.{fmt}"
        assert run("plan", str(EX / "sepsis.yaml"), "--org", str(ORGF), "--format", fmt, "-o", str(out)) == 0
        assert out.read_text().strip()
    assert "Risk tier: **high**" in (tmp_path / "o.md").read_text()
    assert "<!doctype html>" in (tmp_path / "o.html").read_text()


def test_init_roundtrip(tmp_path):
    f = tmp_path / "a.yaml"
    assert run("init", "-o", str(f)) == 0
    assert run("validate", str(f)) == 0
    assert run("plan", str(f)) == 0


def test_validate_catches_bad_answer(tmp_path, capsys):
    f = tmp_path / "bad.yaml"
    f.write_text("answers:\n  function: magic\n")
    assert run("validate", str(f)) == 1
    assert run("plan", str(f)) == 2


def test_fail_on_open():
    assert run("plan", str(EX / "sepsis.yaml"), "--fail-on-open") == 1


def test_web_command(tmp_path):
    out = tmp_path / "p.html"
    assert run("web", "--org", str(ORGF), "-o", str(out)) == 0
    assert "Example Health System" in out.read_text()


def test_sources_and_tier_flag(capsys):
    assert run("sources") == 0
    assert "J13" in capsys.readouterr().out
    assert run("plan", str(EX / "scheduling.yaml"), "--tier", "high") == 0


def test_example_results_locked(capsys):
    from medon import engine
    import yaml
    want = {"sepsis": ("high", 35), "scribe": ("moderate", 30), "scheduling": ("low", 13)}
    for name, (tier, n) in want.items():
        d = yaml.safe_load(open(EX / f"{name}.yaml"))
        p = engine.build_plan(d["answers"])
        assert (p["tier"], p["total"]) == (tier, n), name


def test_md_has_references():
    import yaml
    from medon import engine, render
    d = engine.load_all()
    a = yaml.safe_load(open(Path(__file__).resolve().parents[1] / "examples" / "sepsis.yaml"))["answers"]
    md = render.render_md(engine.build_plan(a, None, None, d), {}, None, d)
    assert "## References" in md and "NIST AI 100-1" in md
