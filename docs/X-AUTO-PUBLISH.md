# Automatic X updates

The workflow publishes to **@MosulOnSol** after a project pull request is merged into `main`.

## What triggers a post

If the merged change adds exactly one new `approved` item to `social/updates.json`, the workflow publishes that exact, fact-checked text. Otherwise, if the merge changes project files, it publishes a concise status based on the merged pull-request title and links directly to that pull request. Queue-only changes without an approved item do not post. The workflow does not publish raw commit messages or changes from unmerged pull requests.

The merged pull request is the public approval point for its title and changes. Keep the title factual, concise, and free of secrets or private customer information. Posts use English and fit X's 280 weighted-character limit.

## Connect the X account

Create an X Developer App authorized for **OAuth 1.0a User Context** with read-and-write permission for `@MosulOnSol`. Add these repository secrets in GitHub under **Settings → Secrets and variables → Actions**:

- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

Generate the user access token and secret while signed in as the project account. Never put credentials in a commit, issue, pull request, or chat. The workflow has read-only repository permission and passes X credentials only to the publishing step.

A merged change triggers one attempt. The workflow does not automatically retry failed or ambiguous requests, to prevent duplicate posts. An HTTP error means no successful publication was confirmed; inspect the X account before a manual retry. X may require eligible developer access and available API credits.

X docs: [Create Posts](https://docs.x.com/x-api/posts/create-posts) · [Authentication overview](https://docs.x.com/fundamentals/authentication/overview)
