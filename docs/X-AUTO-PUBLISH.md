# Automatic X updates

The project publishes a short English update to **@MosulOnSol** when one new approved item is added to `social/updates.json` on `main`.

## What triggers a post

The workflow watches only `social/updates.json`. It posts only when a commit adds exactly one new item whose `status` is `approved`. Code changes and commit messages never post by themselves. The workflow publishes the exact text in the file; it does not generate or embellish claims.

Example entry (replace the ID and text with a fact-checked post):

```json
{
  "updates": [
    {
      "id": "2026-10-12-site-update",
      "status": "approved",
      "text": "MOSUL HERITAGE update: ... https://mosulonsol-max.github.io/MOSUL-HERITAGE-STORE/ #MOSUL"
    }
  ]
}
```

Use a unique ID for each post. Updates must be ASCII English and fit X's 280 weighted-character limit; URLs count as 23 characters. Keep statements about token association, payments, NFTs, sales, and launch status consistent with the verification documents.

## Connect the X account

Create an X Developer App authorized for **OAuth 1.0a User Context** with read-and-write permission for `@MosulOnSol`. Add these repository secrets in GitHub under **Settings → Secrets and variables → Actions**:

- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

Generate the user access token and secret while signed in as the project account. Never put credentials in a commit, issue, pull request, or chat. The workflow has read-only repository permission and passes X credentials only to the publishing step.

Until all four secrets are set, nothing can be published. X may require an eligible developer account or API access plan. The workflow does not automatically retry a failed or ambiguous post, to prevent accidental duplicates; check the account before trying again.

X docs: [Create Posts](https://docs.x.com/x-api/posts/create-posts) · [Authentication overview](https://docs.x.com/fundamentals/authentication/overview)
