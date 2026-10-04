# Contributing

## Add a framework or regulation
1. Add each clause as a control in `src/medon/data/sources.yaml`: id, framework key, clause, requirement paraphrase, status `draft`.
2. Add the framework to the `frameworks` block with title, publisher, date and URL.
3. Either cite the new controls from existing items, or add items in `items.yaml`.
4. Run `pytest`. One test fails if a control is not used by any item.

## Add or change an item
Each item has a phase, action, evidence, owner role, source controls and a minimum tier. Set `sourced: false` and `sources: []` if no clause requires it. Use short sentences.

## Check a control against its source
All controls start as `draft`. If you check one against the source document, open a pull request with the page or section you checked. Once two people have checked it, change `status` to `validated`.

## Rules
No patient data in examples. Keep the questionnaire short. Every question must change the plan. Test files go in `tests/`.
