# AI governance workflow failure — 12 October 2026

## What the email reported

GitHub Actions run `38268175665` failed in the `AI governance checks / test` job at approximately 18:09 Baghdad time. The workflow email was correct when sent.

## Root cause

The new Ed25519 provenance test imported Python's `cryptography` package, but the first version of the governance workflow executed tests before installing `requirements.txt`. GitHub's clean runner therefore raised `ModuleNotFoundError: No module named 'cryptography'`.

## Correction and evidence

The workflow was changed to install pinned runtime dependencies before running tests. The next runs `38268294309` and `38268440330` passed, and the post-merge `main` run `38268534538` also passed. GitHub Pages deployment `38268533206` passed.

No payment, token transfer, secret disclosure, artwork sale, or Mainnet action occurred during the failed run. The failure was a missing CI dependency, not a failure of the policy rules themselves.
