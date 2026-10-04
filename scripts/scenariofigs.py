"""Figures for the 100 scenario run."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import scenarios as sc  # noqa: E402
from medon import engine  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BG, INK, MUT = "#ffffff", "#16191d", "#5d6570"
TIER = {"high": "#c2462b", "moderate": "#c98a12", "low": "#2c8a6e"}
ST = {"done": "#2c8a6e", "in progress": "#c98a12", "open": "#c2462b"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "text.color": INK, "axes.edgecolor": MUT,
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "figure.facecolor": BG, "axes.facecolor": BG})


def main():
    rows, plans, data = sc.main.__wrapped__() if hasattr(sc.main, "__wrapped__") else sc.main()
    A = sc.A
    order = sorted(range(len(A)), key=lambda i: (-["low", "moderate", "high"].index(plans[(i, 2)]["tier"]), A[i][0]))
    items = data["items"]["items"]
    ph_order = [p["id"] for p in data["items"]["phases"]]
    items = sorted(items, key=lambda it: (ph_order.index(it["phase"]), it["id"]))
    M = np.zeros((len(items), len(A)))
    for c, i in enumerate(order):
        ids = {it["id"] for it in plans[(i, 2)]["items"]}
        for r, it in enumerate(items):
            M[r, c] = it["id"] in ids
    fig = plt.figure(figsize=(11, 9.2))
    ax = fig.add_axes([0.31, 0.02, 0.57, 0.62])
    for r in range(len(items)):
        for c in range(len(A)):
            col = TIER[plans[(order[c], 2)]["tier"]] if M[r, c] else "#eef0f3"
            ax.add_patch(plt.Rectangle((c, r), 0.9, 0.86, color=col, lw=0, alpha=1 if M[r, c] else .6))
    ax.set_xlim(0, len(A)); ax.set_ylim(len(items), 0)
    ax.set_yticks([r + .43 for r in range(len(items))]); ax.set_yticklabels([f"{it['id']}  {(it['title'] if len(it['title'])<=46 else it['title'][:45].rstrip()+'...')}" for it in items], fontsize=7.5)
    ax.set_xticks([]); [s.set_visible(False) for s in ax.spines.values()]; ax.tick_params(length=0)
    prev = None
    for r, it in enumerate(items):
        if it["phase"] != prev and prev is not None:
            ax.axhline(r - .07, color=MUT, lw=.6, ls=(0, (1, 3)))
        prev = it["phase"]
    for c, i in enumerate(order):
        ax.text(c + .45, -0.35, A[i][0], rotation=55, ha="left", va="bottom", fontsize=7.2, rotation_mode="anchor")
    fig.text(0.02, 0.985, "Plan items that apply to each of 20 project types", fontsize=12, weight="bold", va="top")
    fig.text(0.02, 0.955, "Filled cell: item applies. Color is the computed risk tier.", fontsize=9, color=MUT, va="top")
    for k, (t, x) in enumerate((("high", .02), ("moderate", .09), ("low", .19))):
        fig.patches.append(plt.Rectangle((x, .918), .012, .014, transform=fig.transFigure, color=TIER[t]))
        fig.text(x + .017, .918, t, fontsize=9, va="bottom")
    fig.savefig(ROOT / "results/figure3.png", dpi=200); fig.savefig(ROOT / "results/figure3.pdf"); plt.close(fig)

    # figure 4
    S = __import__("json").load(open(ROOT / "results/scenarios.json"))
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 4.3), gridspec_kw={"width_ratios": [1.05, 1]})
    labels = list(S["maturity"])
    short = ["None", "Owner and\ncommittee", "Partial", "Strong", "Full"]
    bottom = np.zeros(5)
    for k in ("done", "in progress", "open"):
        v = np.array([S["maturity"][m][k] / S["maturity"][m]["total"] * 100 for m in labels])
        a.bar(range(5), v, bottom=bottom, color=ST[k], width=.62, label=k)
        for x, (vv, bb) in enumerate(zip(v, bottom)):
            if vv > 7: a.text(x, bb + vv / 2, f"{vv:.0f}%", ha="center", va="center", color="#111" if k == "in progress" else "white", fontsize=8.5)
        bottom += v
    a.set_xticks(range(5)); a.set_xticklabels(short, fontsize=8.5); a.set_ylim(0, 100); a.set_ylabel("Share of plan items (%)")
    a.set_title("Plan status by governance maturity", loc="left", fontsize=11, weight="bold")
    a.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(.5, -.2), fontsize=8.5)
    for s in ("top", "right"): a.spines[s].set_visible(False)
    qs = [q["id"] for q in data["questionnaire"]["questions"] if q["type"] != "status"]
    vals = [S["unsure"]["bump_by_question"].get(q, 0) for q in qs]
    idx = np.argsort(vals)[::-1]
    b.barh(range(len(qs)), [vals[i] for i in idx], color="#c2462b", height=.62)
    for k, i in enumerate(idx): b.text(vals[i] + .2, k, str(vals[i]), va="center", fontsize=8.5)
    b.set_yticks(range(len(qs))); b.set_yticklabels([qs[i] for i in idx], fontsize=8.5); b.invert_yaxis()
    b.set_xlabel("Archetypes whose tier rises (of 20)"); b.set_xlim(0, 13)
    b.set_title("Tier change when one answer is unsure", loc="left", fontsize=11, weight="bold")
    for s in ("top", "right"): b.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(ROOT / "results/figure4.png", dpi=200); fig.savefig(ROOT / "results/figure4.pdf"); plt.close(fig)


if __name__ == "__main__":
    main()
