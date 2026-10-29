# Assessment template and Comparison & conclusion contract

## 1. Per-architecture final assessment (Round 3)

```markdown
<a id="a<k>-final"></a>
### Architecture <k> – Final assessment

**Strengths** – bullets, each with the notes ID that supports it.
**Weaknesses** – bullets with IDs.
**Risks / what will hurt after one year** – numbered, most severe first (support load, stuck states,
data growth, boundary erosion, vendor/outage dependencies …).
**Cost & team (relative)** – deployables, pipelines, team size, infra relative to the simplest option;
estimate date; [unverified] if not checked.
**Lock-in & exit** – what is portable, what is sticky, exit options + rough effort.
**Compliance impact** – what changes for privacy/regulation in this style.
**Devil's advocate** – "what is left of this style's promise?" – honest answer.
**Verdict** – one or two sentences: when this style would be the right choice.
```

## 2. Comparison & conclusion contract (Phase 3)

The `architecture-decision-record` skill reads this section. Keep the headings and IDs.

```markdown
## Comparison & conclusion

<a id="h1"></a>
### H1 – Critique of the runner-up / hybrid
What it really adds, what it costs (all known costs from the notes), verdict.

<a id="c0"></a>
### C0 – Assumptions and decision drivers
**Assumptions** (confirmed by the user): numbered list – scale, peaks, team, regulation, payments model …
**Decision drivers in priority order** (confirmed by the user): D1 … Dn, each one line, with the
reason why it has this rank.
**Driver definitions:** what each driver includes and excludes (no fact counted twice); name the
definition choice that could flip a comparison and justify the chosen one.

<a id="c1"></a>
### C1 – Comparison table
| Driver | Option A | Option B | … |
|---|---|---|---|
| D1 … | **Strong** – reason (ID) | **Weak** – reason (ID) | … |
Ratings: Strong / Acceptable / Weak. **Decision rule:** compare driver by driver in priority order;
the first driver where options differ decides. Costs as relative estimates with date.
**Rule check:** state which driver decides between the winner and each other option.
**Sensitivity tests:** table *test (swap adjacent drivers / alternative definition / runner-up's best
driver first) → deciding driver → winner*; conclude what the recommendation depends on.

<a id="c2"></a>
### C2 – Recommendation
Chosen option + what it concretely includes (processes, stores, key rules) + why (link to drivers).
**Would change if:** table *condition → then* (link each condition to an assumption).

<a id="c3"></a>
### C3 – Architecture-independent decisions
| Area | Decision | Source IDs |
(valid for any option; candidates for separate ADRs)

<a id="c4"></a>
### C4 – Open questions and assumptions to verify
Grouped: with the client / legal-compliance / during implementation.
```

Before presenting C1–C2: run the rule check. If the recommended option does not win under the stated
rule, either a rating or the recommendation is wrong – fix it and tell the user what changed.
