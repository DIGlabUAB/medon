"""Write the reviewer workbook for the planned two reviewer validation.
One scenario per archetype at maturity M2. Reviewers rate every plan item and list missing items."""
import csv, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src"))
import scenarios as SC
from medon import engine

def main():
    data = engine.load_all()
    out = ROOT / "validation"; out.mkdir(exist_ok=True)
    rows = []
    for i, (name, _, ans) in enumerate(SC.A):
        p = engine.build_plan({**ans, **SC.maturity(2)}, None, None, data)
        for it in p["items"]:
            rows.append([f"s{i+1:02d}", name, p["tier"], it["id"], it["title"], it["phase"],
                         "", "", ""])
    with open(out / "reviewer workbook.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "project type", "computed tier", "item id", "item", "phase",
                    "rating (1 appropriate, 2 appropriate with changes, 3 not appropriate)",
                    "comment", "reviewer"])
        w.writerows(rows)
    with open(out / "missing items.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "project type", "missing item (free text)", "source document if known", "reviewer"])
        for i, (name, _, _) in enumerate(SC.A):
            w.writerow([f"s{i+1:02d}", name, "", "", ""])
    print(len(rows), "rows")

if __name__ == "__main__":
    main()
