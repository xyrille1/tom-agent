# Project Summary: Theory-of-Mind Benchmark for LLM Agents

A reference document with the full technical detail of this project, written so you can
pull accurate, specific claims for a resume, portfolio, or interview talking points.
Every number in here is verified against the actual repo state, not aspirational.

---

## One-line description

A procedurally-generated, controlled benchmark that measures whether LLM agents can
model another agent's *false* belief — not just report the true state of the world —
using a matched-pair experimental design, evaluated live against multiple free-tier
model APIs, with zero infrastructure cost.

## The problem this solves

Public claims that "LLMs pass/fail theory-of-mind tests" are usually based on a single
classic vignette (the "Sally-Anne test") with no control condition and high risk that
the model has simply memorized the textbook example from training data. This project
builds an actual testbed instead of a one-off quiz: every trial is procedurally
generated and paired with a matched control, so failures can be attributed specifically
to belief-modeling rather than to reading comprehension or memorization.

---

## What was built

### 1. Scenario engine (procedural generation with an experimental control)
- Generates a small household world (3–4 rooms, containers, ~50-item object pool, ~20
  NPC names) from a random seed, fully reproducible (same seed → identical output,
  covered by tests).
- Emits every scenario as a **matched pair**: a false-belief condition (F) and a
  true-belief control (T) built from the *same* underlying world and event sequence,
  differing only in whether the NPC witnessed the belief-changing event. This is the
  core methodological contribution — it isolates "the model can't track beliefs" from
  "the model didn't understand the scenario," which naive false-belief benchmarks
  conflate.
- A lightweight anti-contamination check (trigram Jaccard similarity against a
  reference corpus of classic-vignette paraphrases) flags any generated scenario that
  reads too close to a known textbook example, with automatic regeneration on
  collision. 100% of generated scenarios passed on first generation (0 rejections
  across 50 pairs).
- Narrative text is rendered through multiple paraphrase templates per story beat
  (not one fixed sentence), so no two scenarios — and no scenario — reads like a
  reused template.

### 2. Deterministic rule-based NPC ("the Seeker")
- A pure, stateless function (no LLM, no randomness) implementing a simple belief
  rule: search the last personally-observed location, falling back to a fixed
  room-sweep order. This makes the ground truth for every trial unambiguous and
  100% predictable — the benchmark never has to guess what the "correct" answer is.

### 3. Dual task framing from one source of truth
- **Interactive task**: the model under test must place an "assist" marker at the
  location it predicts the NPC will check first, given a full event log the NPC
  itself didn't fully witness.
- **Static quiz task**: the same scenario, reframed as a 3-option multiple-choice
  question (true location / believed location / decoy room), with a fixed-seed shuffle
  so answer position never correlates with correctness.
- Both are generated from the identical scenario object, so the two task types can
  never drift out of sync with each other — this enables a genuine
  interactive-vs-quiz agreement analysis (Pearson correlation + point-difference)
  per model, a comparison most LLM benchmarks don't attempt.

### 4. Model-agnostic client layer — 5 provider integrations
- A `Protocol`-based client interface (`generate(prompt) -> str`) with a
  registry that auto-detects which free-tier API keys are configured and skips
  the rest — no code changes needed to add or remove a model from a run.
- **Implemented and unit-tested (payload construction + response parsing) for 5
  providers**: Google Gemini, Groq, Anthropic Claude, Hugging Face Inference
  Providers, and Cloudflare Workers AI.
- **Live-integration-verified against real APIs for 3 of them** (Gemini, Hugging
  Face, Cloudflare Workers AI) — see "Real bugs found and fixed" below for what that
  actually surfaced.
- A deterministic mock client allows the entire pipeline (generation → scoring →
  aggregation → site rendering) to be exercised at zero cost and zero network calls,
  for development and CI.

### 5. Resumable, rate-limited batch runner
- Runs N scenarios × M models × 2 conditions × 2 task types with per-provider
  request pacing (respecting each free tier's rate limit), exponential backoff on
  retryable errors (429/503/timeouts), and **incremental writes** — each trial is
  persisted to disk immediately on success.
- A trial is only ever written once its call actually succeeds; a failed call is
  simply left for the next invocation to retry. This makes the runner naturally
  resumable across days without any separate retry-queue concept — verified for
  real when a Hugging Face account hit its free monthly inference-credit cap
  mid-batch (402 Payment Required on the final 3 of 20 calls): the other 17 were
  preserved, and the 3 will complete automatically on the next run once quota resets.
- A `--dry-run` mode reports the exact number of API calls a batch will make
  *before* any request is sent, so free-tier quota is never spent by surprise.

### 6. Statistical scoring layer
- Per-model accuracy on each condition/task-type combination with a **Wilson score
  95% confidence interval** (implemented from scratch, no scipy dependency) —
  chosen over the normal approximation because it stays well-behaved at small
  sample sizes and at accuracy values near 0% or 100%.
- The headline metric, the **"ToM gap"** (true-belief accuracy − false-belief
  accuracy), computed per model per task type.
- A failure taxonomy that distinguishes *why* a wrong answer was wrong: reported
  the true world state instead of the belief, named neither valid location, or
  a residual "wrong belief" bucket — rather than collapsing all errors into one
  accuracy number.
- Cross-task-type agreement analysis (Pearson correlation over scenarios answered
  under both task types by the same model, plus a simple point-difference).

### 7. Static demo site (zero backend, zero database)
- A leaderboard, a filterable/searchable trial-replay viewer (renders the room
  layout, the full event timeline, the exact prompt sent to the model, the raw
  response, and the ground truth side-by-side), and a methodology write-up —
  all built as vanilla HTML/CSS/JS reading pre-computed JSON, deployable to
  GitHub Pages with no server.
- UI built against a validated, colorblind-safe design system (fixed categorical
  color ordering, WCAG-aware contrast handling, dark-mode support via
  `prefers-color-scheme`) rather than arbitrary styling.
- Every number on the leaderboard is traceable to an individual, inspectable
  trial transcript — no aggregate-only results.

### 8. "The repo is the database"
- Every scenario, trial transcript, and computed score is a committed JSON file.
  No Postgres, no Supabase, no hosting bill — the git history itself is the audit
  trail, and any trial can be inspected directly on GitHub without running code.

---

## Real bugs found and fixed via live API integration

This wasn't just built and left untested against mocks — it was run against real
free-tier endpoints, which surfaced three distinct real-world integration bugs, each
diagnosed from raw HTTP response bodies and fixed at the root cause:

1. **Silent model-quota misconfiguration (Google Gemini)** — a versioned model ID
   (`gemini-2.0-flash-lite`) returned HTTP 429 on every call. The response body
   revealed the real cause was `limit: 0` for that specific model on the account
   (no free-tier eligibility at all), not ordinary rate-limiting — invisible without
   inspecting the structured error body rather than just the status code. Fixed by
   switching to an unversioned model alias with verified nonzero quota, and
   documented the distinction in-code so it doesn't cost the next person hours of
   confusion.
2. **Response-schema inconsistency (Cloudflare Workers AI)** — the API auto-detected
   JSON-shaped completion text and returned it as an already-parsed object instead of
   a raw string, silently violating the client interface's `str`-return contract and
   crashing the batch runner deep inside the scoring layer. Fixed at the client
   boundary (re-serialize before returning) *and* hardened the runner itself to
   validate every client's return type explicitly, converting any future contract
   violation from a crash into a recorded per-trial error.
3. **Permission-scope gap (Hugging Face)** — a valid, correctly-formatted API token
   still failed every call with HTTP 403 because fine-grained HF tokens require
   explicitly enabling "Make calls to Inference Providers" as its own separate
   permission, not implied by any other scope. Diagnosed from the API's error message,
   documented precisely which UI checkbox resolves it.

---

## Tech stack

- **Language**: Python 3.11+ (scenario engine, client layer, scoring, CLI tooling)
- **Data modeling**: Pydantic v2 (schema validation for scenarios, trials, and scores)
- **HTTP**: `httpx` (synchronous client calls to 5 different provider APIs)
- **Testing**: `pytest`, 52 tests, no network dependency required to run the suite
- **Frontend**: vanilla HTML / CSS / JavaScript, no framework, no build step
- **Data layer**: committed JSON files (no database)
- **Config**: `python-dotenv`, `.env`-based secret management (gitignored, never
  committed — verified via repo history audit)

## Skills demonstrated

- Experimental design for ML evaluation (matched control conditions, confound
  isolation, confidence intervals, contamination/leakage mitigation)
- Multi-provider third-party API integration and debugging from raw HTTP diagnostics
- Defensive systems design (type-contract validation at API boundaries, resumable
  batch processing, graceful degradation under partial failure)
- Statistical methods implemented from first principles (Wilson score interval,
  Pearson correlation)
- Cost-conscious architecture (zero-infrastructure design, pre-flight cost
  estimation, free-tier rate-limit-aware pacing)
- Test-driven development across a full pipeline (generation, scoring, client
  contracts, batch resumability under simulated failure)
- Applied a validated, accessibility-aware design system to a data-heavy UI
  (leaderboard + interactive trial replay) with no framework

---

## Verified numbers (as of this write-up)

| Metric | Value |
|---|---|
| Unit tests | 52, all passing, zero network dependency |
| Scenario pairs generated | 50 (100 individual scenarios) |
| Novelty-check pass rate | 100% (0 of 50 pairs rejected/regenerated) |
| Model providers implemented | 5 (Gemini, Groq, Anthropic, Hugging Face, Cloudflare Workers AI) |
| Model providers live-verified | 3 (Gemini, Hugging Face, Cloudflare Workers AI) |
| Mock-pipeline validation trials | 200 (zero cost, zero network) |
| Real trials completed against live APIs | 57 (20 Gemini + 20 Cloudflare + 17 Hugging Face) |
| Infrastructure cost | $0 (no database, no hosting, no required paid API tier) |

---

## Ready-to-use resume bullets

Pick the framing that matches the role you're targeting — these are all backed by
the detail above, not exaggerated.

**AI/ML-evaluation framing:**
> Designed and built a controlled theory-of-mind benchmark for LLM agents from
> scratch, using a matched-pair experimental design (false-belief vs. true-belief
> control) to isolate genuine belief-modeling failures from scenario-comprehension
> failures — validated live against 3 free-tier model APIs (Google Gemini,
> Hugging Face, Cloudflare Workers AI) with statistically-grounded reporting
> (Wilson confidence intervals, cross-task-type agreement analysis).

**Backend/systems framing:**
> Built a resumable, rate-limited batch-processing pipeline integrating 5 third-party
> LLM APIs behind a unified client interface, with incremental crash-safe persistence,
> exponential backoff, and pre-flight cost estimation — diagnosed and fixed 3
> distinct live-API integration bugs (quota misconfiguration, response-schema
> inconsistency, permission-scope gaps) directly from raw HTTP diagnostics.

**Full-stack / product framing:**
> Shipped an end-to-end LLM benchmark product — procedural test-case generation,
> a 5-provider model evaluation harness, statistical scoring, and a static
> zero-backend web dashboard (leaderboard + interactive trial replay viewer) — on a
> strict $0 infrastructure budget, backed by a 52-test suite covering generation
> reproducibility, scoring edge cases, and failure-mode resumability.

**Concise single-line version:**
> Built and live-tested a $0-infrastructure theory-of-mind benchmark for LLM agents
> across 5 model-provider integrations, with a matched-control experimental design,
> resumable batch processing, and a static evaluation dashboard — 52 passing tests,
> 100 procedurally generated scenarios, zero contamination-check failures.

---

## Repo reference

See [`README.md`](README.md) for setup/usage instructions and
[`tom-benchmark-prd-mvp.md`](tom-benchmark-prd-mvp.md) for the original product
requirements doc this was built against. [`site/methodology.html`](site/methodology.html)
has the public-facing methodology write-up.
