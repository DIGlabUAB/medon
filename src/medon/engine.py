"""Rule engine. Turns answers into a tier and a plan. No network, no data leaves the machine."""
from __future__ import annotations

from importlib import resources

import yaml

TIERS = ["low", "moderate", "high"]
STATUS_VALUES = ["yes", "partial", "no", "unsure"]


def _load(name):
    return yaml.safe_load(resources.files("medon").joinpath("data", name).read_text(encoding="utf-8"))


def load_all():
    return {
        "questionnaire": _load("questionnaire.yaml"),
        "tiering": _load("tiering.yaml"),
        "items": _load("items.yaml"),
        "sources": _load("sources.yaml"),
    }


def normalize(answers):
    """YAML turns unquoted yes and no into booleans. Map them back to strings."""
    out = {}
    for k, v in (answers or {}).items():
        if v is None or v == "" or v == []:
            continue
        if v is True:
            v = "yes"
        elif v is False:
            v = "no"
        elif isinstance(v, list):
            v = [("yes" if x is True else "no" if x is False else x) for x in v]
        out[k] = v
    return out


def validate_answers(answers, questionnaire):
    """Return a list of problems. Missing answers are allowed and treated as unsure."""
    problems = []
    qs = {q["id"]: q for q in questionnaire["questions"]}
    for k, v in answers.items():
        if k not in qs:
            problems.append(f"unknown question id: {k}")
            continue
        q = qs[k]
        if q["type"] == "status":
            allowed = set(STATUS_VALUES)
        else:
            allowed = {o["value"] for o in q["options"]} | {"unsure"}
        vals = v if isinstance(v, list) else [v]
        if q["type"] == "multi" and not isinstance(v, list):
            problems.append(f"{k}: expected a list")
            continue
        if q["type"] != "multi" and isinstance(v, list):
            problems.append(f"{k}: expected one value")
            continue
        for x in vals:
            if x not in allowed:
                problems.append(f"{k}: '{x}' is not one of {sorted(allowed)}")
    return problems


def _leaf_value(answers, qid):
    return answers.get(qid, "unsure")


def evaluate(cond, answers, derived):
    """Return (truth, uncertain). Unsure or missing answers make a leaf true and uncertain."""
    if not cond:
        return True, False
    if "all" in cond:
        rs = [evaluate(c, answers, derived) for c in cond["all"]]
        return all(r[0] for r in rs), any(r[1] for r in rs)
    if "any" in cond:
        rs = [evaluate(c, answers, derived) for c in cond["any"]]
        return any(r[0] for r in rs), any(r[1] for r in rs)
    if "d" in cond:
        t, u = derived[cond["d"]]
        return t, u
    v = _leaf_value(answers, cond["q"])
    vals = v if isinstance(v, list) else [v]
    if "unsure" in vals:
        return True, True
    if "eq" in cond:
        return v == cond["eq"], False
    if "in" in cond:
        return v in cond["in"], False
    if "has" in cond:
        return cond["has"] in vals, False
    if "has_any" in cond:
        return any(x in vals for x in cond["has_any"]), False
    raise ValueError(f"bad condition: {cond}")


def _label(cond):
    if "d" in cond:
        return cond["d"].replace("_", " ")
    key = next(k for k in ("eq", "in", "has", "has_any") if k in cond)
    val = cond[key]
    val = ", ".join(val) if isinstance(val, list) else val
    return f"{cond['q']} {'is' if key == 'eq' else 'is one of' if key == 'in' else 'includes'} {val}"


def explain(cond, answers, derived):
    """List the leaf conditions that are true, for showing why a tier was chosen."""
    if not cond:
        return []
    if "all" in cond:
        return [x for c in cond["all"] for x in explain(c, answers, derived)]
    if "any" in cond:
        out = []
        for c in cond["any"]:
            if evaluate(c, answers, derived)[0]:
                out += explain(c, answers, derived)
        return out
    return [_label(cond) + (" (unanswered or unsure)" if _leaf_unsure(cond, answers, derived) else "")]


def _leaf_unsure(cond, answers, derived):
    if "d" in cond:
        return derived[cond["d"]][1]
    return "unsure" in (answers.get(cond["q"], "unsure") if isinstance(answers.get(cond["q"], "unsure"), list) else [answers.get(cond["q"], "unsure")])


def compute_derived(tiering, answers):
    d = {}
    for name, cond in tiering["derived"].items():
        d[name] = evaluate(cond, answers, {})
    return d


def compute_tier(tiering, answers, derived):
    for t in tiering["tiers"]:
        truth, unc = evaluate(t["when"], answers, derived)
        if truth:
            return t["id"], unc, explain(t["when"], answers, derived)
    return "low", False, []


def compute_profile(tiering, answers):
    """Six axis descriptive profile. Returns a list of {id, label, score, unsure}."""
    out = []
    for ax in tiering["profile"]:
        v = answers.get(ax["q"], "unsure")
        unsure = v == "unsure" or v not in ax["scores"]
        out.append({"id": ax["id"], "label": ax["label"], "score": 2 if unsure else ax["scores"][v], "unsure": unsure})
    return out


def build_plan(answers, org=None, tier_override=None, data=None):
    data = data or load_all()
    org = org or {}
    answers = normalize(answers)
    derived = compute_derived(data["tiering"], answers)
    tier, tier_uncertain, tier_why = compute_tier(data["tiering"], answers, derived)
    computed = tier
    if tier_override:
        if tier_override not in TIERS:
            raise ValueError("tier override must be one of " + ", ".join(TIERS))
        tier = tier_override
    rank = TIERS.index(tier)
    ctl = {c["id"]: c for c in data["sources"]["controls"]}
    fws = data["sources"]["frameworks"]
    roles = (org.get("roles") or {})
    cadence = (org.get("cadence") or {})
    local = (org.get("local_policy") or {})
    all_items = list(data["items"]["items"]) + list(org.get("extra_items") or [])
    out = []
    for it in all_items:
        if TIERS.index(it.get("min_tier", "low")) > rank:
            continue
        truth, unc = evaluate(it.get("applies"), answers, derived)
        if not truth:
            continue
        status = "open"
        sq = it.get("status_q")
        if sq:
            s = answers.get(sq)
            status = {"yes": "done", "partial": "in progress"}.get(s, "open")
        cad = None
        if it.get("cadence"):
            cad = (cadence.get(it["cadence"]) or {}).get(tier) or None
        out.append({
            "id": it["id"],
            "phase": it["phase"],
            "title": it["title"],
            "action": it["action"],
            "evidence": it["evidence"],
            "owner_role": it["owner"],
            "owner": roles.get(it["owner"]) or None,
            "frequency": cad,
            "frequency_needed": bool(it.get("cadence")),
            "status": status,
            "confirm": unc,
            "sourced": it.get("sourced", True),
            "local_policy": local.get(it["id"]),
            "sources": [
                {"id": c, "framework": fws[ctl[c]["framework"]]["short"], "clause": ctl[c]["clause"],
                 "requirement": ctl[c]["requirement"], "status": ctl[c]["status"]}
                for c in it["sources"]
            ],
        })
    counts = {"done": 0, "in progress": 0, "open": 0}
    for i in out:
        counts[i["status"]] += 1
    return {
        "tier": tier,
        "tier_computed": computed,
        "tier_overridden": bool(tier_override) and tier_override != computed,
        "tier_uncertain": tier_uncertain,
        "tier_why": tier_why,
        "profile": compute_profile(data["tiering"], answers),
        "items": out,
        "counts": counts,
        "total": len(out),
        "unanswered": sorted(q["id"] for q in data["questionnaire"]["questions"]
                             if q["type"] != "status" and q["id"] not in answers),
    }
