"""Command line interface."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from . import engine, render, web


def _read_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_inputs(args):
    doc = _read_yaml(args.answers)
    project = doc.get("project") or {}
    answers = engine.normalize(doc.get("answers") or {})
    org = _read_yaml(args.org) if getattr(args, "org", None) else {}
    return project, answers, org


def cmd_init(args):
    data = engine.load_all()
    L = ["# Answer the questions by editing the values. Use the option value shown. Use unsure when you do not know.",
         "# Quote yes and no.", "project:", "  name: ", "  clinical_lead: ", "  date: ",
         "  # tier_override: high", "  # tier_override_reason: ", "answers:"]
    for sec in data["questionnaire"]["sections"]:
        L += ["", f"  # {sec['title']}"]
        for q in data["questionnaire"]["questions"]:
            if q["section"] != sec["id"]:
                continue
            L.append(f"  # {q['text']}")
            if q["type"] == "status":
                L.append("  #   options: yes, partial, no, unsure")
                L.append(f"  {q['id']}: ")
                continue
            for o in q["options"]:
                L.append(f"  #   {o['value']}: {o['label']}")
            L.append(f"  {q['id']}: " + ("[]" if q["type"] == "multi" else ""))
    text = "\n".join(L) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(text)
    return 0


def cmd_ask(args):
    data = engine.load_all()
    answers, project = {}, {}
    project["name"] = input("Project or tool name: ").strip()
    project["clinical_lead"] = input("Clinical lead: ").strip()
    for q in data["questionnaire"]["questions"]:
        print(f"\n{q['text']}")
        opts = ([{"value": s, "label": s} for s in engine.STATUS_VALUES] if q["type"] == "status"
                else q["options"] + ([] if q["type"] == "multi" else [{"value": "unsure", "label": "Not sure"}]))
        for n, o in enumerate(opts, 1):
            print(f"  {n}. {o['label']}")
        raw = input("Number" + (" (comma separated)" if q["type"] == "multi" else "") + ", blank to skip: ").strip()
        if not raw:
            continue
        try:
            picks = [opts[int(x) - 1]["value"] for x in raw.split(",")]
        except (ValueError, IndexError):
            print("  not understood, skipped")
            continue
        answers[q["id"]] = picks if q["type"] == "multi" else picks[0]
    Path(args.output).write_text(yaml.safe_dump({"project": project, "answers": answers}, sort_keys=False), encoding="utf-8")
    print(f"\nwrote {args.output}")
    return 0


def cmd_validate(args):
    data = engine.load_all()
    doc = _read_yaml(args.answers)
    problems = engine.validate_answers(engine.normalize(doc.get("answers") or {}), data["questionnaire"])
    for p in problems:
        print("problem:", p)
    if not problems:
        print("answers file is valid")
    return 1 if problems else 0


def cmd_plan(args):
    project, answers, org = _load_inputs(args)
    data = engine.load_all()
    problems = engine.validate_answers(answers, data["questionnaire"])
    if problems:
        for p in problems:
            print("problem:", p, file=sys.stderr)
        return 2
    override = args.tier or project.get("tier_override")
    plan = engine.build_plan(answers, org, override, data)
    text = render.RENDERERS[args.format](plan, project, org, data)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(text)
    if args.fail_on_open and plan["counts"]["open"]:
        return 1
    return 0


def cmd_web(args):
    org = _read_yaml(args.org) if args.org else {}
    Path(args.output).write_text(web.build_page(org), encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


def cmd_sources(args):
    data = engine.load_all()
    for c in data["sources"]["controls"]:
        print(f"{c['id']}  {data['sources']['frameworks'][c['framework']]['short']}  {c['clause']}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="medon", description="Governance plan generator for clinical AI projects.")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("init", help="write a blank answers file")
    a.add_argument("-o", "--output")
    a.set_defaults(fn=cmd_init)
    a = sub.add_parser("ask", help="answer the questionnaire in the terminal")
    a.add_argument("-o", "--output", default="answers.yaml")
    a.set_defaults(fn=cmd_ask)
    a = sub.add_parser("validate", help="check an answers file")
    a.add_argument("answers")
    a.set_defaults(fn=cmd_validate)
    a = sub.add_parser("plan", help="build the plan")
    a.add_argument("answers")
    a.add_argument("--org", help="institution file")
    a.add_argument("--format", choices=sorted(render.RENDERERS), default="md")
    a.add_argument("--tier", choices=engine.TIERS, help="override the computed tier")
    a.add_argument("--fail-on-open", action="store_true", help="exit 1 if any item is open")
    a.add_argument("-o", "--output")
    a.set_defaults(fn=cmd_plan)
    a = sub.add_parser("web", help="write the single file web form")
    a.add_argument("--org", help="institution file to embed")
    a.add_argument("-o", "--output", default="medon.html")
    a.set_defaults(fn=cmd_web)
    a = sub.add_parser("sources", help="list source controls")
    a.set_defaults(fn=cmd_sources)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
