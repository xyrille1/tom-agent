# Theory-of-Mind Benchmark

A testbed where LLM agents must correctly model another agent's *false* belief — not
just the true state of the world — to succeed at a task. Built to the design in
[`tom-benchmark-prd-mvp.md`](tom-benchmark-prd-mvp.md).

Every scenario is procedurally generated as a **matched pair**: a false-belief trial
(F) where the correct answer requires tracking what a scripted NPC still believes,
and a true-belief control (T) with identical world complexity. The gap between T and
F accuracy is the headline metric — see [`site/methodology.html`](site/methodology.html)
for the full write-up.

**Cost: $0.** No database, no paid hosting, no required API spend. The repo *is* the
database (`data/*.json`, committed), and the demo site is static HTML/JS. Model calls
only ever hit free tiers or a one-time free signup credit, and the pipeline can be
fully exercised with zero API keys via `--mock`. **Verified working against real
free-tier APIs** (Gemini + Cloudflare Workers AI, see the Troubleshooting section for
the exact fixes that got them working) — this isn't just an untested design.

---

## Step by step: how to use this project

Commands below are PowerShell (Windows). If you're on macOS/Linux, swap the venv
activation line for `source .venv/bin/activate` and use `python3`.

### 1. One-time setup

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pytest -q          # confirm the pipeline itself is healthy
```

### 2. Generate scenarios

Procedurally generates matched (F, T) pairs from random seeds, novelty-checked
against a reference corpus of classic vignettes. 50 pairs = 100 scenarios.

```powershell
.venv\Scripts\python.exe scripts\generate_scenarios.py --n 50
```

(Already done once — `data/scenarios/` has 100 files committed. Re-run only if you
want a different N or a fresh set.)

### 3. Try the zero-cost path first

Runs the full pipeline against a deterministic fake model client — no keys, no
network calls, no cost. This is how you confirm the *engine* works before spending
any real quota:

```powershell
.venv\Scripts\python.exe scripts\run_batch.py --mock
.venv\Scripts\python.exe scripts\compute_scores.py
```

### 4. Configure real free-tier models

Copy `.env.example` to `.env` and fill in whichever keys you have — any provider left
blank is automatically skipped:

| Env var | Where to get it | Free tier |
|---|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey | Permanent, no card |
| `GROQ_API_KEY` | https://console.groq.com/keys | Permanent, no card |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com | One-time signup credit, no card charge |
| `HUGGINGFACE_API_KEY` | https://huggingface.co/settings/tokens | Monthly inference credits, no card — **must have "Inference Providers" permission enabled on the token, see Troubleshooting** |
| `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` | https://dash.cloudflare.com | Daily "neurons" allotment, no card — token needs "Workers AI: Read/Edit" scope; account ID is on any dashboard page (not secret) |

`.env` is gitignored — never commit real keys, and avoid pasting them into a chat if
you can help it (putting them straight into `.env` is all this project ever needs).

### 5. Dry-run before spending any quota

Always check the exact call count before it happens:

```powershell
.venv\Scripts\python.exe scripts\run_batch.py --dry-run
```

### 6. Run a small real pilot

```powershell
.venv\Scripts\python.exe scripts\run_batch.py --limit-pairs 5
.venv\Scripts\python.exe scripts\compute_scores.py
```

Watch the console output — each trial prints `[OK]` or `[ERROR]` with the reason live,
so a misconfigured key or wrong model name shows up immediately instead of silently.

### 7. Run the full batch

```powershell
.venv\Scripts\python.exe scripts\run_batch.py
.venv\Scripts\python.exe scripts\compute_scores.py
```

Trials are written incrementally and skipped if already on disk, so if a free-tier
daily cap gets hit partway through, just re-run the same command later (same day or
the next) — it resumes rather than restarting.

### 8. View the results

The site fetches committed JSON via relative paths, so it must be served over HTTP
(not opened as a `file://` URL):

```powershell
.venv\Scripts\python.exe -m http.server 8000
# then open http://localhost:8000/site/index.html
```

- **Leaderboard** (`index.html`) — accuracy, ToM gap, confidence intervals per model.
- **Trial replay** (`replay.html`) — browse/filter individual trials, see the room
  layout, event log, exact prompt, raw model response, and ground truth side by side.
- **Methodology** (`methodology.html`) — the control-condition design, novelty-check
  limitations, and free-tier disclosure.

### 9. (Optional) Publish to GitHub Pages — still $0

1. Push this repo to GitHub.
2. Repo Settings → Pages → Source: **Deploy from a branch** → `main` → `/ (root)`
   (root, not `/docs` — the site fetches `../data/...`, so `site/` and `data/` need
   to be published together).
3. Live at `https://<you>.github.io/<repo>/site/index.html`.

---

## Troubleshooting (real issues hit and fixed during a live pilot run)

- **Gemini 429 with `limit: 0` in the error body, on every call** — this is different
  from a normal rate limit. `limit: 0` means the specific model ID has *no* free-tier
  quota on your account at all, not that you've used it up. Versioned IDs like
  `gemini-2.0-flash-lite` hit this; the unversioned alias `gemini-flash-lite-latest`
  (the current default in `src/tom_bench/clients/gemini.py`) worked. If you hit this
  again, try another `GEMINI_MODEL` override — which model IDs carry free quota shifts
  over time and per account.
- **Hugging Face 403: "This authentication method does not have sufficient
  permissions to call Inference Providers"** — the token exists and is valid, but
  wasn't granted inference access. Fix: go to
  https://huggingface.co/settings/tokens, create a new **fine-grained** token (or edit
  the existing one) and explicitly enable **"Make calls to Inference Providers"**
  under permissions. A token without that scope will 403 regardless of which model
  you target.
- **Cloudflare Workers AI returning parsed JSON objects instead of strings** — some
  Workers AI models auto-detect JSON-shaped output and hand back an already-parsed
  object in `result.response` instead of raw text. This crashed the pipeline the
  first time (real bug, since fixed) — `cloudflare.py` now re-serializes a dict
  response back to a string so scoring's own JSON parsing still works.
- **A bad response from any provider should never crash the whole batch** — as of
  this fix, `runner.py` validates that every client returns a plain string and turns
  any violation into a per-trial `error`, not an uncaught exception. If you write a
  new client, keep that contract.

## Repo layout

```
src/tom_bench/          scenario engine, deterministic Seeker, prompts, scoring, clients, runners
scripts/                 CLI entry points (generate scenarios / run batch / compute scores)
data/scenarios/          generated scenario pairs (committed JSON)
data/trials/             per-trial transcripts (committed JSON)
data/scores.json         aggregated leaderboard numbers (regenerated by compute_scores.py)
data/trials_index.json   lightweight manifest the replay page uses to browse trials
data/reference_corpus/   small fixture corpus for the novelty-check heuristic
site/                     static demo site (leaderboard, replay viewer, methodology)
tests/                    pytest suite
```

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Covers: scenario reproducibility from a seed, F/T pair complexity-matching, the
novelty check (including that it correctly flags an inserted classic vignette),
Seeker logic, answer parsing/scoring/failure-tagging edge cases (including
unparseable output and non-string client responses), Wilson CI bounds, score
aggregation, model client payload/parse functions for all five providers, and
batch-runner resumability under a simulated mid-batch API failure.

## Privacy / secrets

No API keys, tokens, or personal data are committed anywhere in this repo. `.env` is
gitignored; only `.env.example` (with blank placeholders) is tracked. Model client
code never logs key values — only which provider was configured or skipped.
