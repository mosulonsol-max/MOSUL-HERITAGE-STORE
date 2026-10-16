# Free GPU sessions and task split

## Goal

Use free compute for development without making the preview appear to be a completed sale or a continuously available service.

## Task boundaries

| Stage | Runs where | Input | Output / acceptance |
|---|---|---|---|
| Policy tests and repository checks | GitHub Actions (public standard runner) | Current source | Pass/fail logs; no GPU required |
| One image generation | Google Colab free GPU, started interactively | Current public source and fixed prompt | One valid watermarked preview, catalog record, audit log, hash manifest |
| Validation, signing, and publishing | GitHub Actions | Uploaded ZIP from `artwork-data/sessions/latest.zip` | Verified preview deployed to Pages; optional Ed25519 signature from the GitHub Secret |

Each Colab run has one bounded task. The notebook stops if a GPU or valid output is unavailable. It never falls back to a fabricated image. It does not receive wallet, signing, or GitHub write credentials. The GitHub workflow applies the signing key only after it validates the downloaded artifact.

## Run a free session

1. Open the notebook in Google Colab: [MOSUL HERITAGE free GPU session](https://colab.research.google.com/github/mosulonsol-max/MOSUL-HERITAGE-STORE/blob/free-gpu-session-kit/notebooks/mosul_free_gpu_session.ipynb).
2. Choose **Runtime → Change runtime type → T4 GPU** if available, then run all cells from top to bottom.
3. Download `mosul-preview-session.zip`. If the free tier does not offer a GPU, retry later; do not create duplicate accounts or evade service limits.
4. In GitHub, switch to the `artwork-data` branch, upload the ZIP to `sessions/latest.zip`, and commit it.
5. Open **Actions → Publish verified Colab preview → Run workflow** on `main`; retain the default bundle path.
6. Confirm the workflow finished successfully and inspect the deployed preview.

## What this does and does not mean

- The generated item is a **watermarked public preview, not for sale**.
- It is interpretive art, not a verified historical reconstruction; the current generator labels it accordingly.
- The public Colab notebook contains no secrets. Do not paste API keys, wallet material, buyer information, or signing keys into it.
- GitHub's standard hosted runners are free for public repositories, but they do not provide the NVIDIA GPU needed by the current FLUX runner.
- Colab free GPU availability and usage limits vary and are not guaranteed. The notebook is an interactive batch session, not a 24/7 GPU service.
- Free sessions can prove the generation and validation path. They cannot guarantee the project's target of one finished product every hour.

## Cost boundary

The planned workflow uses Colab only for short, interactive generation runs and GitHub Actions for CPU-based checks, artifact validation, signing, and Pages deployment. GitHub Actions does not automatically wake a Colab notebook. Do not enable the existing hourly FLUX runner until a persistent/managed GPU endpoint is configured; otherwise the hourly workflow will not generate an image.
