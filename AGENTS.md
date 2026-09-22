# testing-jev

Experiments with Jev, TypeSafe AI's first System One model. Repo: `rsalas6/testing-jev` (private).

Whatever comes out of here feeds posts on beto.page, written in English.

## How to run

Everything runs in Docker, driven by Task: `task run:test-N-name.py`. See `README.md`.

- One file per experiment: `test-<n>-<topic>.py`, numbered in the order we built them.
- Every script takes `--save` and writes `<script>-output.txt`. Those files are committed so results can be read without spending another call.
- The key lives in `.env` as `TYPESAFE_API_KEY` (see `.env.example`). Never commit `.env`.

## Model notes

- Endpoint: `POST https://api.typesafe.ai/v1/systemone`. Over raw HTTP, `model` is required (`jev-latest`); the SDK fills it in.
- Pricing: $0.042 per million input tokens, output free. There is no usage endpoint, so cost is computed from `usage.input_tokens`.
- `confidence` is derived from the probabilities: `(n * peak - 1) / (n - 1)`. Noul answers don't carry it.
- Answers are not deterministic: the same state moves by a few hundredths between calls.

## GitHub accounts (`gh`) — REQUIRED

Two accounts are logged in: `rsalas6` and `roberto-micro1`.

- **This repo is always worked with `rsalas6`.**
- **The active account must always be left on `roberto-micro1`**, even if the operation fails (chain with `;`, not `&&`).

```sh
gh auth switch -u rsalas6
# ... push, gh pr create, etc ...
gh auth switch -u roberto-micro1
```

## Git

- Commit identity: `Roberto Salas <rsalas0691@gmail.com>`.
- Conventional commit messages.
