# Task 3 – Skills for architecture exploration and ADRs

The skills live where Claude Code discovers them automatically – in the repository's
`.claude/skills/` folder:

| Skill | Use it for | Files |
|---|---|---|
| [`architecture-exploration`](../../.claude/skills/architecture-exploration/SKILL.md) | Propose several architectures from requirements, debate them one at a time (max 3 rounds each), recommend one. Writes notes with IDs and a *Comparison & conclusion* section. | [SKILL.md](../../.claude/skills/architecture-exploration/SKILL.md), [hard-spots checklist](../../.claude/skills/architecture-exploration/references/hard-spots-checklist.md), [failure question bank](../../.claude/skills/architecture-exploration/references/failure-question-bank.md), [assessment template](../../.claude/skills/architecture-exploration/references/assessment-template.md), [notes template](../../.claude/skills/architecture-exploration/references/notes-template.md) |
| [`architecture-decision-record`](../../.claude/skills/architecture-decision-record/SKILL.md) | Turn the notes (own or foreign) into an ADR, self-review it before showing, iterate with a version log. | [SKILL.md](../../.claude/skills/architecture-decision-record/SKILL.md), [ADR template](../../.claude/skills/architecture-decision-record/references/adr-template.md), [review checklist](../../.claude/skills/architecture-decision-record/references/adr-review-checklist.md) |

How they were derived (analysis of the original run, error → rule mapping, coverage of manual requests):
[NOTES.md](NOTES.md).

## Testing the skills
1. Start a **new** Claude Code session in the repository root.
2. Ask without naming the skill (e.g. "navrhni architektúru pre systém v Week_05_Designing/Tasks/data/…")
   and record whether the skill triggered.
3. Outputs of the new run go to `Task_3/run_after/` (not to Task_1/Task_2).
4. Export both sessions: `transcripts/before.md` (original run) and `transcripts/after.md` (run with the skills).
5. Compare using the Run log sections and the transcripts → report in this folder.

## Converting a session log to Markdown
Claude Code stores every session as JSONL in `~/.claude/projects/<project-folder>/<session-id>.jsonl`
(on Windows: `C:\Users\<user>\.claude\projects\c--Users-…-AI4SE-Labs-2026\`). The newest file is
usually the current session; check the first user message to be sure. The script only reads it.

```bash
python -I Week_05_Designing/Task_3/tools/jsonl_to_md.py \
  "C:/Users/<user>/.claude/projects/<project-folder>/<session-id>.jsonl" \
  Week_05_Designing/Task_3/transcripts/after.md \
  "C:/Users/<user>/Documents/MATFYZ/2mAIN/AI/AI4SE_Labs_2026" \
  "Transcript – run with the skills (after)"
```
Arguments: session JSONL, output file, repository root (used to shorten file paths), optional title.
Output: `## User` / `## Assistant` in order, text verbatim, each tool call as one line
`> [tool: <name> <file or description> → ok|error]`, IDE context as one line; reasoning blocks, tool
outputs and system reminders are omitted. The script prints the number of user messages.
