#!/usr/bin/env bash
# Run once from inside the medon folder on your Mac. Needs git and the GitHub CLI (gh auth login).
set -euo pipefail
ORG=DIGlabUAB
REPO=medon
[ -d .git ] || git init -b main
touch docs/.nojekyll
mkdir -p .github/workflows
[ -f .github/workflows/ci.yml ] || cp docs/ci.yml.example .github/workflows/ci.yml
git add -A
git commit -m "Medon 0.1.0" || true
gh repo create "$ORG/$REPO" --public --source=. --push \
  --description "Questionnaire driven governance plans for clinical AI, traced to published frameworks"
gh api -X POST "repos/$ORG/$REPO/pages" -f "source[branch]=main" -f "source[path]=/docs" || \
gh api -X PUT  "repos/$ORG/$REPO/pages" -f "source[branch]=main" -f "source[path]=/docs"
echo "Site: https://diglabuab.github.io/$REPO/  (allow a few minutes)"
