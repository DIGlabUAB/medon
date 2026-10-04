# Medon

Answer a structured questionnaire about a clinical AI project. Get a governance plan and checklist traced to published governance documents. Each health system sets its own roles, committees and review frequencies in one file.

Status: version 0.1.0. Two documents are encoded: NIST AI RMF 1.0 and the Joint Commission and CHAI guidance (September 2025). The encoded clauses are draft until independently reviewed. See `docs/METHOD.md`.

## Use it

Web form, no install. Build one page for your institution and host it on any internal web server.

    pip install medon
    medon web --org my-institution.yaml -o medon.html

The page runs in the browser. No answers leave the machine. Users can print the plan, or save it as Markdown, CSV or JSON.

Command line:

    medon init -o answers.yaml          # blank answers file with all options listed
    medon ask  -o answers.yaml          # or answer in the terminal
    medon plan answers.yaml --org my-institution.yaml --format md -o plan.md
    medon plan answers.yaml --fail-on-open   # exit 1 while items remain open

Formats: `md`, `html`, `json`, `csv`. Examples are in `examples/`.

## What the plan contains

- A risk tier (low, moderate, high) with the reasons.
- 11 to 35 items by phase: governance, before deployment, after go live, change and retirement.
- For each item: what to do, what evidence shows it is done, the owner role, the frequency, and the source clauses.
- A status for each item (done, in progress, open) taken from the "what already exists" questions.
- Items that depend on an unsure answer are marked Confirm. Unsure answers push the tier up.

## Adopt it at your institution

1. Copy `src/medon/data/org.example.yaml`. Fill in role titles, review frequencies by tier and links to your own policies.
2. Add local requirements as `extra_items` with ids that start with L.
3. Build the web page with `medon web --org your-file.yaml`.
4. Edit `tiering.yaml` if your risk triage differs. A project can also override its tier with a stated reason.
5. Add other frameworks or regulations as new controls and items. See `CONTRIBUTING.md`.

The source documents give no review frequencies, no thresholds and no response times. The plan prints "Set by local policy" until your institution fills them in.

## Limits

Medon is a planning aid that supports your governance committee and counsel. The risk tier is a local triage heuristic that you can edit in `tiering.yaml`. FDA, EU AI Act and state law overlays are on the roadmap. The clinician workload item is marked as a local consideration because no encoded clause covers it.

License: Apache 2.0 for code, CC BY 4.0 for data. See `NOTICE`.
