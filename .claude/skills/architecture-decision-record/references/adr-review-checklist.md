# ADR self-review checklist

Run on **every** version before showing it. Report: ✅ passed, 🔧 fixed (what), ⚠️ unverifiable (why).
Each check comes from an error that slipped through in a real review.

| # | Check | How | Prevents |
|---|---|---|---|
| K1 | **Decision rule holds** | Apply the stated rule (driver by driver in priority order) to the table. The chosen option must win; name the deciding driver against each other option. If ratings were numeric, recompute sums/weights too – they must not contradict. | Table contradicting the decision |
| K2 | **Every rating has a source** | For each cell, find the notes ID. Re-read the runner-up's and every hybrid's documented costs and check that each one shows up in some rating. | Ratings ignoring earlier critique |
| K3 | **Driver order = real reasoning** | Compare the order with the "why" of the recommendation in the notes; confirmed by the user? | Wrong priorities |
| K4 | **Rules quoted exactly – and complete** | For every rule in the ADR (e.g. about transactions, I/O, ownership), find the original wording in the notes and compare. No strengthening, weakening or generalising. Then enumerate **all states the rule governs** (e.g. a resource held with / without an external session, decided by a provider fact / by a domain deadline) and check that the quoted rule covers each; if the source rule is too broad or too narrow, propose a Correction in the notes instead of copying it. | Misquoted or over-broad rules |
| K5 | **Diagram ↔ text ↔ context** | Every integration named in Context appears in the deployment view; every rule in "What the decision includes" is visible (sync vs. async edges, webhooks, after-commit calls); labels match the text. Every external system used by a Confirmation check or a risk mitigation (monitor, storage clean-up, …) and every "worker does X with Y" in the notes is an edge. | Diagrams hiding the rules |
| K6 | **Full flow walk-through** | Walk **every** user story plus every assumption with an enforcement point, every timer owner, every back-office action and erasure. For each data item a flow reads or writes, name the **owning module** and the arrow or legend rule that allows it; check that no Confirmation check forbids it. Store the walk-through table in the ADR notes. | Missing flows, diagram contradicting CI checks |
| K7 | **Claim provenance** | Every factual claim (capacity, cost, limits, legal) traces to a notes ID or is moved to Open questions / marked [unverified]. | Unsupported claims |
| K8 | **Assumptions ↔ revisit ↔ TL;DR** | Each revisit trigger cites an assumption; TL;DR names the main trigger and matches the decision. | Inconsistent summary |
| K9 | **Duplicates** | Each fact appears once (consequences vs. table vs. rejected options). | Bloat |
| K10 | **Length budget** | Count words without diagram code and URLs; compare with the budget; cut duplicates first, never content. | Over-long ADR |
| K11 | **Costs age well** | No absolute prices; relative estimates with date and source. | Outdated numbers |
| K12 | **Tests prove properties** | Each Confirmation test asserts the property (e.g. zero deadlocks, exactly N successes), not a tolerated violation; undefined targets → Open questions. | Weak confirmation |
| K13 | **Legal / compliance wording** | Applicability states the real trigger; "not legal advice" where relevant. | Wrong legal statements |
| K14 | **Mermaid renders** | Try to render (local renderer / CLI if allowed). If not possible: label "[unverified render]" and ask the user to check in mermaid.live or the GitHub preview. Use standard syntax: `flowchart`, quoted labels, `-->|"label"|`. | Broken diagrams |
| K15 | **Links resolve** | Every `#anchor` link exists in the target notes. | Dead links |
| K16 | **Related decisions** | Each has a one-sentence "already agreed" summary, a status and a source; undecided ones say "not decided yet". | Pointer-only lists |
| K17 | **No invention** | Nothing in the ADR is absent from the notes, except items explicitly marked "Changed by this ADR" at the user's request. | Invented decisions |
| K18 | **Status / metadata** | Proposed during review; Accepted + date only on the user's instruction. | Premature acceptance |
| K19 | **Confirmation coverage** | Each of the top 3 drivers and each key rule in *What the decision includes* has at least one Confirmation check (e.g. negative authorization tests for a security driver; "clients fail inside an open transaction" for a no-network-in-transaction rule). | Unchecked drivers and rules |
| K20 | **Requirements coverage** | Every component, queue, process type or extraction path named in the decision is motivated by a row in the requirements table (and vice versa every row maps to a driver). | Unmotivated components, missing requirements |
| K21 | **Gaps in the source** | For every assumption ask "what does implementing it require that the notes never discussed?" (data sources, providers, costs, privacy). Such items go to Open questions, marked as not from the notes. | Silent gaps (e.g. where coordinates come from) |
