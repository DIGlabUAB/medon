import copy

import pytest

from medon import engine

DATA = engine.load_all()
BASE = {"function": "administrative", "autonomy": "informs", "model_type": "predictive",
        "source": "in_house", "users": ["staff"], "affects_care": "no", "patient_level": "no",
        "harm": "minimal", "phi": "none", "updates": "fixed", "workload": "no"}


def plan(**kw):
    a = copy.deepcopy(BASE)
    a.update(kw)
    return engine.build_plan(a, data=DATA)


def ids(p):
    return {i["id"] for i in p["items"]}


def test_data_integrity():
    src = {c["id"] for c in DATA["sources"]["controls"]}
    qs = {q["id"] for q in DATA["questionnaire"]["questions"]}
    phases = {p["id"] for p in DATA["items"]["phases"]}
    seen = set()
    for it in DATA["items"]["items"]:
        assert it["id"] not in seen
        seen.add(it["id"])
        assert it["phase"] in phases
        assert set(it["sources"]) <= src
        assert it.get("status_q") is None or it["status_q"] in qs
        assert it.get("sourced", True) == bool(it["sources"])
        assert it["min_tier"] in engine.TIERS
    assert len(src) == 107


def test_every_source_control_is_used():
    used = {s for it in DATA["items"]["items"] for s in it["sources"]}
    unused = {c["id"] for c in DATA["sources"]["controls"]} - used
    assert unused == set(), f"controls not reachable from any item: {sorted(unused)}"


def test_low_tier_administrative():
    p = plan()
    assert p["tier"] == "low"
    assert "P04" not in ids(p) and "C03" not in ids(p)
    assert "G01" in ids(p) and "O01" in ids(p)


@pytest.mark.parametrize("kw,tier", [
    ({"function": "diagnostic"}, "high"),
    ({"harm": "serious"}, "high"),
    ({"autonomy": "acts_without_review"}, "high"),
    ({"autonomy": "acts_with_review", "affects_care": "yes"}, "high"),
    ({"function": "clinical_support"}, "moderate"),
    ({"affects_care": "yes"}, "moderate"),
    ({"users": ["patients"]}, "moderate"),
    ({"model_type": "generative", "patient_level": "yes"}, "moderate"),
    ({"model_type": "generative"}, "low"),
])
def test_tier_rules(kw, tier):
    assert plan(**kw)["tier"] == tier


def test_unsure_goes_up():
    p = plan(harm="unsure")
    assert p["tier"] == "high" and p["tier_uncertain"]
    assert any("unanswered or unsure" in w for w in p["tier_why"])


def test_missing_answers_are_unsure():
    p = engine.build_plan({}, data=DATA)
    assert p["tier"] == "high"
    assert len(p["unanswered"]) == 11


def test_tier_override():
    p = engine.build_plan(BASE, tier_override="high", data=DATA)
    assert p["tier"] == "high" and p["tier_overridden"] and p["tier_computed"] == "low"
    with pytest.raises(ValueError):
        engine.build_plan(BASE, tier_override="extreme", data=DATA)


def test_higher_tier_is_superset_of_items_when_other_answers_equal():
    low = ids(engine.build_plan(BASE, tier_override="low", data=DATA))
    mod = ids(engine.build_plan(BASE, tier_override="moderate", data=DATA))
    high = ids(engine.build_plan(BASE, tier_override="high", data=DATA))
    assert low <= mod <= high and low != high


def test_vendor_items():
    p = plan(source="vendor_embedded", updates="vendor_updates", phi="identifiable")
    assert {"P03", "P06", "P07", "C01"} <= ids(p)
    q = plan(source="in_house", updates="vendor_updates", phi="identifiable")
    assert not ({"P03", "P06", "P07", "C01"} & ids(q))


def test_vendor_notice_only_when_vendor_changes_model():
    assert "C01" not in ids(plan(source="vendor_product", updates="fixed"))
    assert "C02" in ids(plan(updates="local_retrain"))


def test_patient_transparency_item():
    assert "P08" in ids(plan(users=["patients"]))
    assert "P08" not in ids(plan())
    assert "P08" in ids(plan(phi="identifiable"))


def test_workload_item_is_marked_unsourced():
    p = plan(workload="yes")
    i = next(x for x in p["items"] if x["id"] == "O09")
    assert i["sourced"] is False and i["sources"] == []
    assert "O09" not in ids(plan(workload="no"))


def test_status_mapping():
    a = {**BASE, "x_owner": "yes", "x_committee": "partial", "x_risk": "no"}
    p = engine.build_plan(a, data=DATA)
    s = {i["id"]: i["status"] for i in p["items"]}
    assert s["G01"] == "done" and s["G02"] == "in progress" and s["P02"] == "open"


def test_yaml_booleans_normalized():
    p = engine.build_plan({**BASE, "affects_care": True, "x_owner": True}, data=DATA)
    assert p["tier"] == "moderate"
    assert next(i for i in p["items"] if i["id"] == "G01")["status"] == "done"


def test_validate_answers():
    q = DATA["questionnaire"]
    assert engine.validate_answers(BASE, q) == []
    assert engine.validate_answers({"function": "magic"}, q)
    assert engine.validate_answers({"nope": "x"}, q)
    assert engine.validate_answers({"users": "staff"}, q)
    assert engine.validate_answers({"x_owner": "maybe"}, q)


def test_org_config_fills_owner_and_cadence():
    org = {"roles": {"governance_lead": "CMIO"},
           "cadence": {"monitoring": {"high": "monthly", "moderate": "quarterly", "low": "annually"}}}
    p = engine.build_plan({**BASE, "harm": "serious"}, org, data=DATA)
    g = next(i for i in p["items"] if i["id"] == "G01")
    o = next(i for i in p["items"] if i["id"] == "O01")
    assert g["owner"] == "CMIO" and o["frequency"] == "monthly"
    q = engine.build_plan(BASE, data=DATA)
    assert next(i for i in q["items"] if i["id"] == "O01")["frequency"] is None


def test_org_extra_items_and_local_policy():
    org = {"extra_items": [{"id": "L01", "phase": "govern", "title": "Local", "action": "x", "evidence": "y",
                            "owner": "governance_lead", "sources": [], "sourced": False, "min_tier": "low"}],
           "local_policy": {"G02": "Charter 4.12"}}
    p = engine.build_plan(BASE, org, data=DATA)
    assert "L01" in ids(p)
    assert next(i for i in p["items"] if i["id"] == "G02")["local_policy"] == "Charter 4.12"


def test_option_labels_are_complete():
    for q in DATA["questionnaire"]["questions"]:
        for o in q.get("options", []):
            assert o["label"].count("(") == o["label"].count(")")
        assert q["text"].endswith((".", "?"))
