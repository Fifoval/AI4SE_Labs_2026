---
name: architecture-exploration
description: >-
  Interactive, round-based exploration of software architecture options from requirements (user
  stories, SRS, feature lists). Use whenever the user wants to propose, design, brainstorm, compare,
  challenge or choose an architecture or architecture style for a system – e.g. "propose an
  architecture", "design the system architecture", "compare architectures", "which architecture should
  we choose", "monolith vs microservices", "should we go serverless", "discuss architecture options",
  "navrhni architektúru", "porovnaj architektúry", "ktorú architektúru zvoliť", "prebrať architektúry",
  "návrh architektúry systému", "monolit alebo mikroslužby". Presents architectures one at a time,
  asks targeted questions, takes positions, covers failure scenarios proactively, keeps structured
  notes with IDs and ends with a Comparison & conclusion section that the architecture-decision-record
  skill consumes. Not for writing the ADR document itself.
---

# Architecture exploration

Goal: the user ends up **understanding** each candidate architecture (trade-offs, painful low-level
parts, failure modes) and has a justified recommendation – recorded in notes that can feed an ADR.
This is a **dialogue, not a report**.

## Ground rules (apply in every round)

1. **Language.** These instructions are English. Talk to the user in **their** language. Write the
   notes in English unless the user asks otherwise.
2. **Round budget.** One round = **max 5–7 points + 2–3 questions for the user**, then **stop and wait**.
   Never cover two architectures in one round. Max **3 rounds per architecture** (see Phase 2).
3. **Understanding check.** In every round at least one question asks the user to *explain or predict*
   something ("why does this not oversell?", "what happens if the process crashes between X and Y?").
4. **Take positions.** State what you recommend and why. If the user's argument is better, say so
   plainly ("you are right"), change the decision and record a **Correction** in the notes.
5. **Answer the user's questions first**, completely, point by point; then continue the plan.
6. **Fast mode.** If the user says "fast mode" / "rýchly režim": merge the rounds of an architecture
   into one, keep the full coverage in the notes, and ask only about decisions you need from them.
7. **Requirements-driven, not copy-driven.** Derive everything from the given requirements. Do not
   reuse solutions from other projects; use the references only as generic checklists.
8. **Verify facts** about external APIs, limits, prices, platform capabilities and legal rules:
   use web search when available and cite sources; otherwise mark the claim **[unverified]** in the
   chat and the notes. Never present remembered vendor details as current facts.
9. **Write notes continuously** (`references/notes-template.md`): after every round, before replying.
   Decisions, corrections and open questions get stable IDs.

## Correctness rules (learned from earlier reviews – check before every reply)

| Rule | What to do |
|---|---|
| R1 Justify every protection layer | For each mechanism (lock, retry, TTL, extra capture step, safety net) name the failure it prevents and check whether an earlier layer already prevents it. Drop redundant layers. |
| R2 Verify external facts | See ground rule 8. Typical traps: deprecated batch APIs, changed limits, plan quotas, regional availability. |
| R3 Enumerate states | For every idempotent, compensating or "upsert-like" operation list **all** pre-existing states (absent / in progress / done / cancelled / rejected) and the effect on **every invariant** (e.g. returned quantity). Code snippets must handle each state. |
| R4 Timeouts from the domain | Derive every timeout/TTL from domain constraints (event start time for tickets, check-in date for hotel rooms, flash-sale end, legal deadlines, provider limits), never from generic defaults. Say where the number comes from. |
| R5 Async triggers overlap | When work is started asynchronously (cron firing HTTP, webhooks, queues), check overlapping executions, concurrency limits and rate limits explicitly. |
| R6 Real security semantics | For each security mechanism state its exact semantics: row vs. column, owner vs. invoker rights, per role vs. per user, default grants. |
| R7 Tests prove the property | A proposed test must verify the property itself (e.g. zero deadlocks), not tolerate its violation through a safety net (retries). |
| R8 Legal/compliance wording | State the actual legal trigger (establishment, target users, activity) and mark "not legal advice – verify". |
| R9 Costs | Give relative costs (×A1, team size) with the date of the estimate; absolute numbers only as [unverified] ranges. |
| R10 No network inside a transaction | Never show a code path that calls an external system (payment provider, e-mail, push, HTTP) while a DB transaction or row lock is open. Use claim (short tx) → call (no tx) → apply only a **terminal** external fact (short tx, conditional transition). State this for every snippet that talks to an external system. |
| R11 Decide at the owner | Irreversible decisions about money or scarce resources are taken by the owner of the fact over its authoritative state, atomically – never from a read model, a cached copy or the *absence* of an event (timeouts). Timers that cancel another component's step *ask* that component. |
| R12 Order of "record" vs. "act" | For every side effect decide which failure is acceptable: notifications → mark first, then send (at most one lost); money → call with an idempotency key first, then record (never "done" without the effect). Say which order and why. |

## Workflow

### Phase 0 – Setup (one exchange)
1. Find the requirements (ask for the file/system if unclear).
2. Ask in one message: number of architectures (default 3 + possible hybrid), the user's goal (learn
   deeply vs. decide fast → fast mode), known constraints (team size, budget, deadline, compliance,
   regions, mobile clients), notes location (default: next to the task, `NOTES.md`).
3. Create the notes from `references/notes-template.md`; fill **Run log → start time**.

### Phase 1 – Requirements analysis (one round)
Use `references/hard-spots-checklist.md`. Present:
- actors/roles (watch for several roles on one account),
- core domain concepts and their lifecycles,
- **which hard-spot categories apply**, each with the user-story references,
- **explicit assumptions** (scale, peaks, team, budget, regulation, clients) – **each with its impact on
  the choice of style** ("favours few deployables", "scale is not a driver", …) – ask the user to confirm
  or correct them now (they become the ADR's assumptions),
- **operations model**: who reacts to alerts at night/weekends (none → automatic remediation rules and
  alert routing by risk become a design topic, see the failure bank),
- **candidate styles**: 3 genuinely different styles chosen for *this* system's hard spots – from e.g.
  layered or modular monolith, microservices, event-driven / event sourcing + CQRS, serverless / BaaS,
  space-based, pipeline / batch, micro-frontends – with one sentence why each fits, and whether a hybrid
  is worth evaluating. Do not default to a fixed trio.
Ask the user to approve the candidates. Do not start an architecture before that.

### Phase 2 – One architecture at a time (max 3 rounds each)

**Round 1 – Big picture and hard spots**
- Components / services / modules, **data ownership**, communication rule (sync vs. async).
- A small diagram (Mermaid or ASCII) of processes and external systems.
- For every applicable hard spot: the concrete mechanism (with a short code/SQL/pseudo-code snippet for
  the riskiest one), applying R1–R6.
- Proactively include: the **inventory of time-driven behaviour** (every deadline/timer: trigger,
  owner, action, how it is safe to run twice) and **what we actually deploy** (process types, stores,
  external services).
- Questions: one understanding check + 1–2 design choices the user should make.

**Round 2 – Failure scenarios**
- Pick the relevant sections of `references/failure-question-bank.md` (cross-cutting + this style).
- Present the **5–7 most dangerous failures for this system**, each as: scenario → consequence →
  fix (with ID). List the remaining relevant questions from the bank in one line and offer to go deeper.
- Ask the user which failure to examine further, plus one understanding check.

**Round 3 – Final assessment**
- Fill the per-architecture block of `references/assessment-template.md`: strengths, weaknesses,
  risks after one year of operation, honest cost (relative), team/ops burden, lock-in and exit plan,
  compliance impact, **devil's advocate: "what is left of this style's promise?"**, verdict.
- Ask whether anything is unclear before moving to the next architecture.

If the user asks follow-up questions, answer them inside the current round budget; a fourth round
for one architecture only on the user's explicit request (log it in the Run log).

### Phase 3 – Comparison & conclusion (1–2 rounds)
Follow the **Comparison & conclusion contract** in `references/assessment-template.md` exactly – the
ADR skill relies on it:
1. **Critique the runner-up and every hybrid** with *all* their known costs before recommending.
2. **Decision drivers:** derive them from the discussion, propose a priority order and **ask the user to
   confirm/reorder**. The order must match the real reasoning. **Define each driver precisely** (what it
   includes and excludes) so that no fact is counted under two drivers; say which definition choice could
   flip a comparison (e.g. "operability" = only things to run vs. also silent failures and testability).
3. **Comparison table** with verbal ratings (Strong / Acceptable / Weak + one-sentence reason with a
   notes ID). No stars, no sums. State the **decision rule**: compare driver by driver in priority
   order; the first difference decides. **Check mechanically** that the recommended option wins under
   this rule; if not, fix the ratings or the recommendation and tell the user.
   **Sensitivity test (mandatory):** re-run the rule with (a) every pair of adjacent drivers above the
   deciding one swapped, (b) the alternative definition of the deciding driver, (c) the runner-up's best
   driver moved to first place. Present a small table *test → deciding driver → winner* and state which
   choices the recommendation depends on; those become explicit justifications or "would change if" rows.
4. **Recommendation** + **conditions under which it would change** (linked to assumptions).
5. **Architecture-independent decisions** (valid for any option) – table with notes IDs.
6. **Open questions and assumptions to verify** (client / legal / implementation).

### Phase 4 – Notes hygiene and hand-off
- Contents list, "how to read", *superseded → ID* markers on outdated statements, HTML anchors
  `<a id="…"></a>` before every ID'd item (blank line before, no content change).
- Close the **Run log** (end time, totals).
- Offer the `architecture-decision-record` skill for the ADR.

## Notes discipline (summary – details in the template)
- Every discussion item gets an ID (`A<k>.<n>` for architecture k, `H<n>` hybrid critique,
  `C<n>` comparison). Decisions are written as **Decision:**, corrections as **Correction:** with
  what was wrong and who found it.
- Record the user's own proposals and arguments, not only yours.
- Facts from the web: source URL in the notes. Unverified facts: **[unverified]**.

## Run log (mandatory)
Maintain the Run log table in the notes: start/end time, each round (architecture, round type, topics),
**the number of user prompts**, and **what the user had to request that this skill did not cover
proactively**. This is the basis for later before/after comparisons – keep it honest.

## References
- `references/hard-spots-checklist.md` – generic hard-spot categories with cues and questions.
- `references/failure-question-bank.md` – failure questions per style, each with what it reveals.
- `references/assessment-template.md` – per-architecture assessment + Comparison & conclusion contract.
- `references/notes-template.md` – notes structure, ID scheme, markers, Run log.
