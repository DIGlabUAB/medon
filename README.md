# Medon

Governance plans for clinical AI projects.

Describe an AI tool in a short questionnaire. Medon gives back a checklist of what to do, who owns it, what evidence shows it is done, and which published guidance asks for it.

**[Open the planner](https://diglabuab.github.io/medon/app/)** · [Website](https://diglabuab.github.io/medon/) · [Example plans](https://diglabuab.github.io/medon/scenarios/)

Free and open source. Runs in your browser. Nothing you enter is sent anywhere.

## What you get

- A risk tier (low, moderate or high) and the answers that set it.
- A checklist of 11 to 35 items across four phases: governance, before deployment, after go-live, and change and retirement.
- For each item: the action, the evidence, the owner role, how often to review it, and the source clauses.
- A status for each item (done, in progress, open), based on what you said already exists.
- Downloads as Markdown, HTML, CSV or JSON.

If you are unsure of an answer, Medon assumes the safer option and marks the affected items to confirm.

## Built on

107 controls from 10 published documents: NIST AI RMF 1.0, Joint Commission and CHAI guidance, CHAI Responsible AI Guide, CHAI Assurance Standards Guide, CHAI Applied Model Card, EU AI Act (high-risk requirements), ISO/IEC 42001, WHO guidance on AI for health, ONC HTI-1, and FDA guidance on predetermined change control plans. See the [sources page](https://diglabuab.github.io/medon/sources/).

## Use it at your institution

```
pip install git+https://github.com/DIGlabUAB/medon
curl -o my-institution.yaml https://raw.githubusercontent.com/DIGlabUAB/medon/main/src/medon/data/org.example.yaml
# edit my-institution.yaml: your roles, committees, review schedules
medon web --org my-institution.yaml -o planner.html   # one self-contained page for your intranet
```

Until your institution fills in review frequencies, the plan says "Set by local policy". The published guidance does not set them.

Local requirements go in the same file as `extra_items`. Risk tier rules are in `tiering.yaml` and can be edited.

## Command line

```
medon init -o answers.yaml                               # blank answers file
medon ask  -o answers.yaml                               # or answer in the terminal
medon plan answers.yaml --org my-institution.yaml --format md -o plan.md
medon plan answers.yaml --fail-on-open                   # exit 1 while items are open
```

Examples are in `examples/`.

## Good to know

Medon is a planning aid. It supports, and does not replace, your governance committee and legal counsel. The controls are paraphrases drafted with the help of a language model and are marked `draft` until someone checks them against the source; corrections are welcome. The EU AI Act and HTI-1 entries are practice references, not a compliance determination.

## Contribute

Add a framework, fix a control or suggest an item: see [CONTRIBUTING.md](CONTRIBUTING.md) or [open an issue](https://github.com/DIGlabUAB/medon/issues).

Built by the Diagnostic Intelligence Group and Health System Information Services at the University of Alabama at Birmingham. Code under Apache 2.0, data under CC BY 4.0. See `NOTICE`.
