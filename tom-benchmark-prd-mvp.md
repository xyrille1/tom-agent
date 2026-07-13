# Theory-of-Mind Benchmark Agent — PRD + MVP Plan

**Project:** A testbed where agents must model other agents' beliefs — including *false* beliefs — to succeed at a task, used to benchmark how well LLM-based agents reason about others' mental states.

**Status:** Draft v1 — locked decisions below, ready to build against.

**Locked decisions (from your answers):**
- Purpose: public demo **and** methodologically solid (both matter — this shapes almost every choice below)
- Task paradigm: interactive belief-dependent game as the **primary** benchmark, static false-belief Q&A as a **secondary** set (lets you compare the two and report whether results transfer)
- Stack: recommended below, rationale included
- **Budget: $0 on your end.** The plan below runs entirely on free-tier infrastructure — no hosting bill, no database bill, no required API spend. Deliverable is a GitHub repo (code + committed result data), optionally rendered via GitHub Pages.

---

## 1. Introduction / Overview

Frontier LLMs are increasingly deployed as agents that act on behalf of, alongside, or in response to other agents (human or AI). Many of those interactions require the model to reason about what *another* party knows or believes — which is often different from what the model itself knows. Classic developmental psychology (Sally-Anne, false-belief tasks) tests exactly this capacity in children. The literature on LLM theory-of-mind (ToM) is active but contested: some results claim near-human performance, others show that performance collapses under reworded, novel, or interactive versions of the same tests, and it's often unclear whether a model is reasoning about beliefs or just pattern-matching a familiar vignette shape.

This project builds a **testbed**, not a single quiz: a procedurally-generated, interactive environment where an LLM agent must correctly attribute a *false belief* to a scripted NPC in order to complete a cooperative task, plus a matched **control condition** (true-belief version of the same scenario) so failures can be attributed specifically to belief-modeling rather than scenario comprehension. A secondary static Q&A benchmark, generated from the same scenario engine, lets us check whether interactive-task performance and quiz performance agree.

The deliverable is public-facing (a leaderboard + replay viewer + methodology writeup) **and** methodologically defensible (novel scenarios to avoid contamination, a control condition, multiple models compared, reproducible scoring).

## 2. Goals / Objectives (SMART)

1. Ship an MVP that runs at least **3 models** through at least **50 paired scenarios** (100 trials: 50 false-belief + 50 matched true-belief control) within the MVP build window, with results published on a public leaderboard.
2. Demonstrate a measurable **"ToM gap"** metric per model: `accuracy(true-belief control) − accuracy(false-belief condition)`. A gap near 0 = model isn't distinguishing belief states; a large gap = model performs worse specifically when it must model a false belief.
3. Confirm or refute, with data, whether **interactive-task accuracy and static-quiz accuracy agree** per model (Pearson/point-difference reported, not just eyeballed).
4. Guarantee **zero scenario reuse** across the classic literature — every trial is procedurally generated from randomized parameters, verified against a simple novelty check.
5. Produce one public artifact (demo + leaderboard + short methodology writeup) usable as a portfolio/differentiator piece within the MVP timeline.

## 3. Target Audience / Personas

- **Primary (public demo viewers):** other developers, AI-curious hiring managers/clients, and ML-community readers (e.g., Twitter/X, Hacker News, LinkedIn) who want a quick, credible, visual sense of "do LLM agents actually model beliefs, or do they just look like they do."
- **Secondary (you, as builder/operator):** uses this as a differentiator artifact in freelance pitches — needs the writeup and results to hold up to scrutiny from a technically literate reader, not just look nice.
- There is no end-"user" workflow beyond viewing results and (optionally) triggering/replaying a trial — this is a benchmark artifact, not a SaaS product.

## 4. Core Concept — Task Design (the part the prior analysis flagged as missing)

### 4.1 Primary task: "Fetch Assist" (interactive, task-success framing)

**World:** a small procedurally laid-out set of 2–4 rooms, each containing a handful of containers (box, drawer, basket) and everyday objects (rotating pool of ~50 items — never "Sally/Anne/basket/marble," to dodge the classic vignette).

**Roles:**
- **NPC Seeker** — fully **scripted, deterministic**, *not* an LLM. Rule: "search the last location I personally observed the target object being placed in; if not found there, fall back to a fixed room-order sweep." Because the Seeker is scripted, its behavior is 100% predictable given its belief state — this gives an unambiguous ground truth and avoids testing two noisy LLMs against each other at once.
- **Subject Agent (the model under test)** — the **Helper**. It observes the *entire* event log (full information, including events the Seeker did not witness). Before the Seeker acts, the Helper must place a single "assist" (a marker/reward) at the location it predicts the Seeker will check first.

**Trial sequence:**
1. Object X is placed in Location P. Seeker is present and observes this.
2. Seeker leaves to Location Q (narrated).
3. **Belief-inducing event:** while the Seeker is away, Object X is moved to Location R.
4. Subject Agent (with full event log, including the move the Seeker never saw) must choose where to place the assist.
5. **Scoring:** task succeeds iff the assist location matches the location the Seeker will actually check first.
   - **False-belief condition (F):** correct answer = P (Seeker's last-known belief), *not* R (the true state). A model that just uses its own true-state knowledge will get this wrong.
   - **True-belief / control condition (T):** identical world and move event, except the Seeker is present for (or is truthfully told about) the move. Correct answer = R. Same surface complexity as F — only the Seeker's awareness differs.

Every generated scenario is emitted as a **matched pair** (F, T) from the same underlying world state, which is what makes the control condition valid — it isolates "can't model beliefs" from "can't parse the scenario," per the earlier analysis's top recommendation.

### 4.2 Secondary task: static false-belief Q&A

Same scenario generator, same matched-pair (F, T) structure, but instead of an interactive assist action, the model is asked directly: *"Where will [Seeker] look for [object] first?"* — multiple choice (true location / believed location / a decoy room), graded by string/location match. Cheap to run at higher volume; used to check whether interactive and quiz-style results agree (Goal #3).

### 4.3 Novelty / anti-contamination

- Object pool, room count, NPC names, and narrative phrasing are all randomized per trial from a seed.
- Narrative flavor-text uses templated slot-filling with several paraphrase variants per slot (not a single fixed sentence), so no two trials — and no trial — reads like a textbook Sally-Anne paragraph.
- A lightweight novelty check (n-gram overlap against a small corpus of known classic vignettes) flags any generated scenario that drifts too close to a known example, for regeneration.

### 4.4 Difficulty tiers

- **Tier 1 (MVP scope):** single NPC, single false-belief event, 0–1 distractor events, first-order belief only ("what does the Seeker believe").
- **Tier 2 (post-MVP):** multiple distractor/move events, a "lied to" condition (NPC is told something false rather than just absent).
- **Tier 3 (post-MVP):** second-order beliefs ("what does A think B believes"), multiple NPCs, communication between NPCs.

MVP builds and validates Tier 1 only — this keeps the scope to a single, well-controlled paradigm rather than trying to cover all ToM task types at once (the prior analysis's #1 warning).

## 5. User Stories / Use Cases

- As a visitor to the demo site, I can see a leaderboard ranking models by F-condition accuracy, T-condition accuracy, and the ToM gap, so I can quickly judge which models actually model false beliefs.
- As a visitor, I can open an individual trial and "replay" it — see the room layout, the event log, and the model's assist placement or quiz answer, with the ground truth highlighted — so I can sanity-check the benchmark isn't rigged or trivial.
- As a technically literate reader, I can read a short methodology page explaining the control condition, novelty-check approach, and why this differs from a plain Sally-Anne prompt, so I trust the result.
- As the operator, I can run a new batch of N scenarios against a configured list of models via a script and have results land in the database and show up on the leaderboard, so adding a new model or growing the sample size doesn't require rebuilding anything.

## 6. Functional Requirements

**Scenario Engine (Python)**
- FR1: Generate a Tier-1 world (rooms, objects, containers) from a random seed.
- FR2: Generate a matched (F, T) pair from one underlying world + move event.
- FR3: Run the novelty check against a small reference corpus; regenerate on collision.
- FR4: Emit both the interactive "Fetch Assist" framing and the static Q&A framing from the same scenario data (shared source of truth — no drift between the two task types).
- FR5: Persist every generated scenario (world state, event log, both framings, ground-truth answers) as a JSON file committed to the repo (`data/scenarios/*.json`) — no database required.

**Agent Harness (Python)**
- FR6: Deterministic Seeker NPC — pure function of belief state, no LLM call, unit-testable in isolation.
- FR7: Model-agnostic client layer that can call models via free-tier APIs with a consistent prompt/response contract — see §9 for the specific free-tier providers this targets.
- FR8: Run a trial: feed the Subject Agent the full event log + task framing, parse its assist location / quiz answer, score against ground truth, store the raw transcript.
- FR9: Batch runner: run N scenarios × M models × 2 conditions (F/T) × 2 task types (interactive/quiz), with retries, **free-tier rate-limit pacing** (spaced requests + exponential backoff on 429s, since free tiers cap requests/minute and requests/day), and writing results incrementally (not all-or-nothing) so a run can pause and resume across multiple days if a daily quota is hit.

**Scoring & Metrics**
- FR10: Per-model accuracy on F, accuracy on T, ToM gap (T − F), 95% confidence interval (binomial) for each.
- FR11: Per-model agreement between interactive-task and quiz-task accuracy.
- FR12: Failure taxonomy tagging (at minimum: "used true state instead of belief," "malformed/unparseable response," "picked neither location").

**Static Demo Site (GitHub Pages)**
- FR13: Leaderboard page — table of models × metrics from FR10/FR11, sortable, built as a static page that reads the committed results JSON (no backend, no API calls at view time).
- FR14: Trial replay view — renders the room/object layout, the event log as a short timeline, and the model's answer vs. ground truth, again reading straight from committed JSON.
- FR15: Static methodology page describing the design, the control condition, and the novelty-check approach in plain language.

**Data**
- FR16: Repo-committed JSON files for scenarios, trials, model responses, and computed scores (see §10) — the repo *is* the database.

## 7. Non-Functional Requirements

- **Reproducibility:** every scenario is generated from a stored seed; re-running a seed reproduces the identical world and event log.
- **Zero required cost:** the whole pipeline must run on free-tier services only — free-tier model APIs, no database service, no paid hosting. Batch runner supports a dry-run / call-count-estimate mode before running any batch, so you always know how many free-tier requests a run will consume before it starts.
- **Extensibility:** adding a 4th model or a Tier-2 scenario type should not require touching the scoring or demo layers — scenario schema and model client interface are the seams.
- **Latency:** demo pages should load from pre-computed/stored results (not live LLM calls) — the public site never calls a model API at request time.
- **Transparency:** every leaderboard number must be traceable to a stored trial the visitor can open and inspect (no aggregate-only results).

## 8. Assumptions & Open Questions (carried over from the prior analysis, now resolved or explicitly flagged)

| Item | Resolution |
|---|---|
| Which task paradigm? | Interactive "Fetch Assist" (primary) + static Q&A (secondary), both from one scenario engine — **resolved** |
| Control condition? | Matched (F, T) pair per scenario, mandatory — **resolved** |
| Contamination risk? | Procedural generation + paraphrase variants + novelty check — **resolved for MVP**; the novelty check is a heuristic, not a guarantee, and should be called out as a limitation in the methodology page |
| How many models? | 3 for MVP, all reachable at **$0**: Google Gemini Flash/Flash-Lite (permanent free tier, no card), an open-weight model via Groq's free tier, and Anthropic Claude run on the one-time free signup credit ($5, no card charge) sized to stay within it — **flagged as an assumption to confirm before build**, since free-tier terms and limits shift over time |
| Deliverable format? | Public leaderboard + replay viewer + methodology writeup — **resolved** |
| Interesting output: accuracy, or failure-mode analysis? | Both — FR12's failure taxonomy feeds the methodology writeup, accuracy feeds the leaderboard — **resolved** |
| Does the "reasoning about beliefs" framing hold, or is this surface pattern completion? | Not resolved by design alone — this is exactly what the T vs. F gap is measuring, and the methodology page should present the gap as evidence, not proof, of genuine belief modeling |

## 9. Tech Stack & Rationale (zero-cost version)

- **Scenario engine + agent harness + scoring: Python**, run locally on your machine (or in a free GitHub Actions runner). Not CrewAI — CrewAI's Crew/Task abstraction is built for *collaborating* agents working a shared task list, not a deterministic, partial-observability environment where one NPC's belief state must be precisely controlled and must not be an LLM at all. A plain Python harness (Pydantic for the scenario schema, `httpx`/`asyncio` for calls, spaced out to respect free-tier rate limits) gives full control at no framework cost.
- **Data store: none.** Scenarios, trials, and computed scores are plain JSON files committed to the repo under `data/`. No Postgres, no Supabase, no database bill, and it doubles as a transparent, inspectable audit trail — anyone can open a trial's JSON directly on GitHub.
- **Model access — all free-tier:**
  - **Google Gemini (Flash / Flash-Lite)** via Google AI Studio — permanent free tier, no card required. Rate-limited (~15 requests/min, ~1,500/day as of mid-2026), which is comfortably enough for this MVP's trial counts once the batch runner paces requests.
  - **An open-weight model via Groq's free tier** — fast, free inference for models like Llama, giving a second $0 comparison point.
  - **Claude**, run once using Anthropic's one-time $5 free signup credit (no card charge). Given how small each trial's prompt/response is, this comfortably covers a few hundred Claude trials — size the Claude portion of the batch to stay inside that credit.
  - Free-tier terms change without much notice (Google has cut free quotas before), so the batch runner's dry-run mode (NFR above) should always be run first, and the methodology page should note which tier/date the free-tier numbers were captured under.
- **Public demo: a static site, not a Next.js app with a backend.** Either (a) a simple static HTML/JS page (can still use React/Tailwind, just exported statically) that reads the committed JSON and renders the leaderboard + replay view, or (b) skip a built page entirely for v0 and let the README + linked JSON/markdown files in the repo *be* the demo. Either way: **GitHub Pages**, free, no server.
- **Hosting:** none required beyond GitHub itself (repo + optional Pages). The Python engine never needs to run as a persistent server — it's a script you run on demand, locally or via a free GitHub Actions workflow, that commits new results back to the repo.

## 10. Data Model (high level — repo layout, not database tables)

- `data/scenarios/<id>.json`: seed, tier, world (rooms/objects/containers), event_log, pair_id (links to its matched F/T counterpart), created_at
- `data/trials/<id>.json`: scenario_id, model_name, task_type (interactive | quiz), raw_response, parsed_answer, is_correct, failure_tag, latency_ms, created_at
- `data/scores.json`: one derived summary file, regenerated by the scoring script after each batch run — model_name, task_type, condition, accuracy, ci_low, ci_high, n. This is the single file the static demo site actually reads for the leaderboard.

---

## 11. MVP Concept

**1. Core MVP Hypothesis:** Frontier LLM agents show a measurable accuracy drop when they must act on another agent's *false* belief versus the *true* state of the world, even when scenario complexity is held constant via a control condition — and this gap is at least partly present regardless of whether the task is framed as an interactive assist-game or a static quiz.

**2. Target Audience (MVP subset):** Public demo visitors evaluating your technical work (portfolio/differentiator use case) — no authenticated users, no accounts.

**3. Problem Solved (MVP focus):** Existing casual claims about "LLMs pass/fail ToM tests" are usually based on a single classic vignette with no control condition and high contamination risk. The MVP produces a small but methodologically sound, novel, controlled dataset and result set that a technical reader can actually trust and inspect.

**4. Minimum Feature Set**

**IN:**
- Tier-1 scenario generator with matched (F, T) pairs (FR1–FR5)
- Deterministic Seeker NPC (FR6)
- Model client layer for 3 free-tier models: Gemini Flash/Flash-Lite, a Groq-hosted open model, Claude (on the one-time free credit) (FR7)
- Interactive "Fetch Assist" trial runner + static Q&A trial runner (FR8, FR4)
- Batch runner over ~50 scenario pairs × 3 models × 2 task types = 600 trials, paced to respect free-tier rate limits and sized to stay inside Claude's free credit (FR9)
- Core metrics: per-model F accuracy, T accuracy, ToM gap, CI (FR10)
- Basic failure tagging: true-state-used vs. false-belief-used vs. unparseable (FR12, minimal version)
- Static leaderboard page on GitHub Pages, or README tables as a v0 fallback (FR13)
- Trial replay view for at least a subset of trials (FR14)
- Methodology writeup page, including a note on which free-tier terms/limits were in effect when results were captured (FR15)
- Committed JSON data files as the data layer (FR16)

**OUT (explicitly deferred):**
- Tier 2/3 scenarios (distractor events, lying NPCs, second-order beliefs, multiple NPCs)
- More than 3 models
- Live/on-demand trial running from the public site (all results are pre-computed and committed)
- User accounts, submitting your own model, community leaderboard
- Any paid model tier or paid hosting/database — everything must fit inside free-tier limits
- Full interactive-vs-quiz statistical agreement testing beyond a simple reported comparison (FR11's deeper analysis is a nice-to-have, not MVP-blocking)
- Automated, guaranteed contamination detection (the novelty check is heuristic, not exhaustive)

**5. Key Constraints:** Solo build; **$0 budget** — every model call must go through a free tier or a one-time free credit, sized so the batch never risks a charge; no database or hosting service, GitHub (repo + optional Pages) is the entire deployment surface; free-tier rate limits (requests/minute and requests/day) mean the full batch run may need to span more than one day, which the batch runner's resumable, incremental writes are designed to handle.

**6. Initial Success Metrics:**
- ToM gap is computable and reported with confidence intervals for all 3 models.
- At least 50 matched scenario pairs pass the novelty check without manual rewriting.
- Demo site loads and every leaderboard number links to an inspectable trial.
- The writeup can survive a technically literate reader asking "how do I know this isn't just Sally-Anne with new names" — i.e., the control condition and novelty check are clearly explained.

---

## 12. MVP Development Plan

### Phase 0 — Design lock (0.5–1 day)
- Finalize the object/room/name pools, the exact Seeker rule ("last observed location, then fixed sweep order"), and the exact prompt contract for the Subject Agent (what it sees, what output format is required).
- Sign up for the 3 free-tier model sources (Google AI Studio for Gemini, Groq, Anthropic Console for the one-time credit) and confirm current free-tier limits — these shift over time, so check the live numbers rather than trusting older documentation.

### Phase 1 — Scenario Engine (2–4 days)
- Build world generator, event log generator, matched (F, T) pair generation.
- Build narrative templating with paraphrase variants.
- Build the novelty check against a small reference corpus of classic vignettes.
- Unit-test: given a seed, output is reproducible; F and T pairs differ only in Seeker awareness, not world complexity.

### Phase 2 — Deterministic Seeker + Trial Runner (2–3 days)
- Implement the Seeker as a pure function (no LLM).
- Implement the interactive "Fetch Assist" trial: build the prompt, call the model, parse the assist location, score.
- Implement the static Q&A trial from the same scenario data.
- Implement failure tagging.
- Develop and test all of this against **mocked model responses** (hardcoded/randomized fake answers) — this is the phase where most bugs surface, and mocking means none of it touches a real API or a free-tier quota.

### Phase 3 — Model Client Layer + Batch Runner (2–3 days)
- Build a consistent client interface across Gemini, Groq, and Claude's real APIs (swapping in for the Phase 2 mocks).
- Build the batch runner with request pacing for each provider's free-tier rate limits, retries with backoff on 429s, incremental writes to `data/trials/`, and a dry-run/call-count-estimate mode.
- Run a small pilot batch (e.g., 5 scenario pairs × 3 models) against the **real free-tier APIs** to validate the pipeline end-to-end — this is the first point real (free) API calls happen.

### Phase 4 — Full Run + Scoring (1 day + run time, possibly spread across days due to daily free-tier caps)
- Generate ~50 scenario pairs, run the full batch (600 trials) — paced to respect Gemini's ~1,500/day and Groq's limits, and sized on the Claude side to stay inside the one-time $5 credit.
- Compute metrics (accuracy, CI, ToM gap, failure tags) and regenerate `data/scores.json`.

### Phase 5 — Static Demo Site (3–5 days)
- Build a static site (or start with README + linked JSON/markdown as v0) that reads `data/scores.json` and individual trial files — no backend, no live API calls.
- Leaderboard page.
- Trial replay view (start with a simple timeline + text rendering of the room/object state; a full animated grid can be a post-MVP polish item).
- Methodology writeup page, including the free-tier disclosure note.
- Publish via GitHub Pages.

### Phase 6 — QA & Launch (1–2 days)
- Run the test plan (§13).
- Spot-check a sample of trials by hand against the stored ground truth to catch scoring bugs.
- Publish.

**Rough total: ~2–3 weeks solo**, excluding Phase 0 design iteration time and whatever cadence you can dedicate around other freelance work.

## 13. Test Plan (highlights)

- **Scenario engine:** same seed → identical output (reproducibility); F/T pairs never differ in room count, object count, or narrative length (complexity-matching check); novelty check correctly flags a deliberately-inserted classic Sally-Anne-style scenario in a test fixture.
- **Seeker logic:** unit tests covering "object never moved," "object moved while present" (should look at new location even in the "F" label — this should never happen by construction, so this test is really checking the generator doesn't produce a broken pair), "object moved while absent," and the fixed-sweep fallback.
- **Scoring:** hand-construct a handful of known-answer trials and confirm the scorer grades them correctly, including edge cases like unparseable model output (should be tagged, not silently scored wrong).
- **Batch runner:** simulate an API failure mid-batch and confirm partial results are preserved and the run is resumable.
- **Demo:** every number on the leaderboard traces to a `trials` row a visitor can open; replay view renders correctly for at least one F and one T trial per model.

## 14. Success Metrics (project-level)

- ToM gap reported for 3 models with confidence intervals.
- 100% of published scenarios pass the novelty check.
- 0 leaderboard numbers without a linked, inspectable trial.
- Public artifact live and shareable within the MVP timeline above.

## 15. Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Novelty check is heuristic, some scenario still resembles a known vignette | Disclose the limitation explicitly in the methodology page; keep the reference corpus small but curated |
| Model output isn't in the expected format (unparseable) | Failure-tag rather than silently scoring wrong; report unparseable rate separately from accuracy |
| Free-tier limits change or shrink mid-project (has happened before with Gemini) | Check live limits at Phase 0 and again right before the full run; dry-run/call-count mode catches a run that's about to exceed quota before it starts |
| Free-tier daily request caps make the full batch take multiple days | Batch runner writes incrementally and is resumable across sessions by design (FR9) |
| Claude's one-time free credit runs out mid-batch | Size the Claude portion of the run to a known-safe trial count before starting, based on the token-cost estimate; if it runs short, that model's sample size can simply be smaller rather than blocking the run |
| Small N (50 pairs) limits statistical confidence | Report confidence intervals honestly rather than point estimates alone; treat MVP as a first data point, not a final claim |
| Interactive and quiz results disagree in a way that's hard to explain | This is itself a reportable finding (per Goal #3) — build the methodology page to present either outcome as informative, not as a bug |

## 16. Next Steps Post-MVP

- Tier 2 (distractor events, lying NPCs) and Tier 3 (second-order beliefs, multiple NPCs) scenario types.
- Grow N and add more models once cost/latency is validated.
- Deeper statistical agreement analysis between interactive and quiz task types (FR11 full version).
- Optional: live "run this model now" trigger from the demo site, gated to protect API cost.
- Optional: animated grid-world replay instead of text-timeline replay.

---

## Open items to confirm before Phase 0 starts

1. **Exact free-tier model picks** — proposed default: Gemini Flash-Lite (free tier), a Groq-hosted open-weight model (free tier), Claude Haiku or Sonnet (one-time free credit, sized to fit). Confirm this set, or swap in different free-tier providers if you have preferences.
2. **Object/room/name pools** — any preference, or should these be generated arbitrarily (e.g., via a fixed curated list you approve once)?
3. **Static site approach** — a built static page (React exported statically, or plain HTML/JS) reading committed JSON, or a leaner v0 that's just README tables + linked trial files? Either is $0; it's a build-time-vs-polish tradeoff.
