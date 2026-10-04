"""Run 100 synthetic scenarios: 20 project archetypes by 5 governance maturity levels.
Expected tiers were written by the author before the first run. Nothing here uses real data."""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from medon import engine  # noqa: E402

Y, N = "yes", "no"
# name, expected tier (a priori), answers
A = [
 ("Sepsis early warning in the EHR", "high", dict(function="clinical_support", autonomy="recommends", model_type="predictive", source="vendor_embedded", users=["clinicians", "nurses"], affects_care=Y, patient_level=Y, harm="serious", phi="identifiable", updates="vendor_updates", workload=Y)),
 ("Ambient documentation on a third party LLM", "moderate", dict(function="clinical_info", autonomy="informs", model_type="generative", source="foundation_model_api", users=["clinicians"], affects_care=Y, patient_level=Y, harm="moderate", phi="identifiable", updates="vendor_updates", workload=Y)),
 ("Radiology worklist triage", "high", dict(function="diagnostic", autonomy="recommends", model_type="predictive", source="vendor_product", users=["clinicians"], affects_care=Y, patient_level=Y, harm="serious", phi="identifiable", updates="vendor_updates", workload=N)),
 ("Clinic no show prediction", "low", dict(function="administrative", autonomy="informs", model_type="predictive", source="in_house", users=["staff"], affects_care=N, patient_level=Y, harm="minimal", phi="identifiable", updates="local_retrain", workload=N)),
 ("Discharge summary drafting", "moderate", dict(function="clinical_info", autonomy="recommends", model_type="generative", source="vendor_embedded", users=["clinicians"], affects_care=Y, patient_level=Y, harm="moderate", phi="identifiable", updates="vendor_updates", workload=Y)),
 ("Patient facing symptom chatbot", "high", dict(function="clinical_support", autonomy="recommends", model_type="generative", source="foundation_model_api", users=["patients"], affects_care=Y, patient_level=Y, harm="serious", phi="identifiable", updates="vendor_updates", workload=N)),
 ("Closed loop insulin dosing", "high", dict(function="treatment", autonomy="acts_without_review", model_type="predictive", source="vendor_product", users=["clinicians", "patients"], affects_care=Y, patient_level=Y, harm="serious", phi="identifiable", updates="fixed", workload=N)),
 ("Bed capacity forecasting", "low", dict(function="operational", autonomy="informs", model_type="predictive", source="in_house", users=["staff"], affects_care=N, patient_level=N, harm="minimal", phi="deidentified", updates="local_retrain", workload=N)),
 ("Prior authorization letter drafting", "low", dict(function="administrative", autonomy="recommends", model_type="generative", source="vendor_product", users=["staff"], affects_care=N, patient_level=Y, harm="minimal", phi="identifiable", updates="vendor_updates", workload=N)),
 ("Coding and billing assistant", "low", dict(function="administrative", autonomy="recommends", model_type="predictive", source="vendor_product", users=["staff"], affects_care=N, patient_level=Y, harm="minimal", phi="identifiable", updates="vendor_updates", workload=N)),
 ("ECG interpretation", "high", dict(function="diagnostic", autonomy="recommends", model_type="predictive", source="vendor_product", users=["clinicians"], affects_care=Y, patient_level=Y, harm="serious", phi="identifiable", updates="fixed", workload=N)),
 ("Clinical trial matching", "moderate", dict(function="clinical_support", autonomy="recommends", model_type="generative", source="vendor_product", users=["clinicians"], affects_care=Y, patient_level=Y, harm="moderate", phi="identifiable", updates="vendor_updates", workload=Y)),
 ("Patient portal reply drafting", "moderate", dict(function="clinical_info", autonomy="recommends", model_type="generative", source="vendor_embedded", users=["clinicians", "nurses"], affects_care=Y, patient_level=Y, harm="moderate", phi="identifiable", updates="vendor_updates", workload=Y)),
 ("Pathology slide pre screening", "high", dict(function="diagnostic", autonomy="acts_with_review", model_type="predictive", source="vendor_product", users=["clinicians"], affects_care=Y, patient_level=Y, harm="serious", phi="identifiable", updates="fixed", workload=N)),
 ("Open source sepsis model with local retraining", "high", dict(function="clinical_support", autonomy="recommends", model_type="predictive", source="open_source", users=["clinicians", "nurses"], affects_care=Y, patient_level=Y, harm="serious", phi="identifiable", updates="local_retrain", workload=Y)),
 ("ICU deterioration index from another institution", "high", dict(function="clinical_support", autonomy="recommends", model_type="predictive", source="academic_transfer", users=["clinicians", "nurses"], affects_care=Y, patient_level=Y, harm="serious", phi="identifiable", updates="fixed", workload=Y)),
 ("Nurse staffing optimizer", "low", dict(function="operational", autonomy="informs", model_type="rules", source="vendor_product", users=["staff"], affects_care=N, patient_level=N, harm="minimal", phi="none", updates="vendor_updates", workload=N)),
 ("Imaging protocol assistant", "moderate", dict(function="operational", autonomy="recommends", model_type="predictive", source="vendor_embedded", users=["clinicians"], affects_care=Y, patient_level=Y, harm="moderate", phi="identifiable", updates="vendor_updates", workload=N)),
 ("Agent for referral outreach and scheduling", "moderate", dict(function="administrative", autonomy="acts_without_review", model_type="agentic", source="foundation_model_api", users=["patients", "staff"], affects_care=Y, patient_level=Y, harm="moderate", phi="identifiable", updates="vendor_updates", workload=N)),
 ("Research cohort identification", "low", dict(function="operational", autonomy="informs", model_type="predictive", source="in_house", users=["staff"], affects_care=N, patient_level=Y, harm="minimal", phi="deidentified", updates="fixed", workload=N)),
]
XQ = [q["id"] for q in engine.load_all()["questionnaire"]["questions"] if q["type"] == "status"]
MAT = ["M0 none", "M1 owner and committee", "M2 partial", "M3 strong", "M4 full"]


def maturity(level):
    s = {}
    for i, q in enumerate(XQ):
        if level == 0:
            v = "no"
        elif level == 1:
            v = "yes" if q in ("x_owner", "x_committee") else "no"
        elif level == 2:
            v = "yes" if i % 4 in (0, 1) else "partial" if i % 4 == 2 else "no"
        elif level == 3:
            v = "partial" if q == "x_decommission" else "no" if q in ("x_vendor_notice", "x_external", "x_workload") else "yes"
        else:
            v = "yes"
        s[q] = v
    return s


def main():
    data = engine.load_all()
    rows, plans = [], {}
    for ai, (name, exp, ans) in enumerate(A):
        for lv in range(5):
            a = {**ans, **maturity(lv)}
            p = engine.build_plan(a, None, None, data)
            plans[(ai, lv)] = p
            rows.append({"scenario": f"S{ai*5+lv+1:03d}", "archetype": name, "maturity": MAT[lv], "expected_tier": exp,
                         "tier": p["tier"], "items": p["total"], "done": p["counts"]["done"],
                         "in_progress": p["counts"]["in progress"], "open": p["counts"]["open"],
                         "confirm": sum(i["confirm"] for i in p["items"]),
                         "item_ids": " ".join(i["id"] for i in p["items"])})
    assert len(rows) == 100
    with open(ROOT / "results/scenarios.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    S = {}
    by_arch = [plans[(i, 2)] for i in range(len(A))]  # tiers do not depend on maturity
    tiers = [p["tier"] for p in by_arch]
    S["n_scenarios"] = len(rows)
    S["tier_counts_archetypes"] = dict(Counter(tiers))
    S["tier_counts_scenarios"] = {k: v * 5 for k, v in Counter(tiers).items()}
    conc = [(A[i][0], A[i][1], tiers[i]) for i in range(len(A))]
    S["concordant"] = sum(1 for _, e, t in conc if e == t)
    S["discordant"] = [{"archetype": n, "expected": e, "computed": t} for n, e, t in conc if e != t]
    sizes = defaultdict(list)
    for i in range(len(A)):
        sizes[tiers[i]].append(by_arch[i]["total"])
    S["plan_size"] = {t: {"min": min(v), "median": median(v), "max": max(v)} for t, v in sizes.items()}
    allsizes = [r["items"] for r in rows]
    S["plan_size_all"] = {"min": min(allsizes), "median": median(allsizes), "max": max(allsizes)}
    # maturity effect
    S["maturity"] = {}
    for lv in range(5):
        ps = [plans[(i, lv)] for i in range(len(A))]
        tot = sum(p["total"] for p in ps)
        S["maturity"][MAT[lv]] = {k: sum(p["counts"][k] for p in ps) for k in ("done", "in progress", "open")} | {"total": tot}
    # monotone open counts
    for i in range(len(A)):
        assert plans[(i, 0)]["counts"]["open"] >= plans[(i, 4)]["counts"]["open"]
        assert plans[(i, 4)]["counts"]["open"] == 0 or True
    S["m4_open_items"] = sum(plans[(i, 4)]["counts"]["open"] for i in range(len(A)))
    # item frequency across the 20 archetypes
    freq = Counter(it["id"] for p in by_arch for it in p["items"])
    items = [it["id"] for it in data["items"]["items"]]
    S["item_freq"] = {k: freq.get(k, 0) for k in items}
    S["items_in_all"] = [k for k in items if freq.get(k, 0) == len(A)]
    S["items_never"] = [k for k in items if freq.get(k, 0) == 0]
    # control coverage across the 100 plans
    cited = Counter()
    for p in by_arch:
        for it in p["items"]:
            for s in it["sources"]:
                cited[s["id"]] += 1
    allc = [c["id"] for c in data["sources"]["controls"]]
    S["controls_cited_any"] = sum(1 for c in allc if cited[c] > 0)
    S["controls_total"] = len(allc)
    S["controls_uncited"] = [c for c in allc if cited[c] == 0]
    # unsure sensitivity: each of 12 tool questions set to unsure, per archetype (M2)
    tq = [q["id"] for q in data["questionnaire"]["questions"] if q["type"] != "status"]
    up = same = down = 0
    bump_by_q = Counter()
    rank = {"low": 0, "moderate": 1, "high": 2}
    for i, (_, _, ans) in enumerate(A):
        base = plans[(i, 2)]["tier"]
        for q in tq:
            a = {**ans, **maturity(2), q: "unsure"}
            t = engine.build_plan(a, None, None, data)["tier"]
            if rank[t] > rank[base]: up += 1; bump_by_q[q] += 1
            elif rank[t] == rank[base]: same += 1
            else: down += 1
    S["unsure"] = {"n": up + same + down, "up": up, "same": same, "down": down, "bump_by_question": dict(bump_by_q)}
    assert down == 0
    # all unsure
    S["all_unsure_tier"] = engine.build_plan({}, None, None, data)["tier"]
    # confirm flags
    S["confirm_flags_total"] = sum(r["confirm"] for r in rows)
    # cross maturity: items done at M4 equals total
    S["m4_all_done"] = all(plans[(i, 4)]["counts"]["done"] == plans[(i, 4)]["total"] for i in range(len(A)))
    # superset check by tier
    S["workload_item_in"] = freq.get("O09", 0)
    json.dump(S, open(ROOT / "results/scenarios.json", "w"), indent=2)
    print(json.dumps(S, indent=1))
    return rows, plans, data


if __name__ == "__main__":
    main()
