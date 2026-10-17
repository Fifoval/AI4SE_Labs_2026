# Task 1 – Prompting Frameworks

## Where I found the frameworks

I found all three frameworks in the [Frompting framework library](https://frompting.com/frameworks).

| ID | Framework | Source | Prompt |
|---|---|---|---|
| P1 | RTF (Role, Task, Format) | [frompting.com/frameworks/rtf](https://frompting.com/frameworks/rtf) | [P1_RTF.md](prompts/P1_RTF.md) |
| P2 | Few-Shot | [frompting.com/frameworks/few-shot](https://frompting.com/frameworks/few-shot) | [P2_FewShot.md](prompts/P2_FewShot.md) |
| P3 | CoT (Chain of Thought) | [frompting.com/frameworks/cot](https://frompting.com/frameworks/cot) | [P3_CoT.md](prompts/P3_CoT.md) |

The prompts are also in [prompts.json](prompts.json), together with their IDs, sources and file paths.

## Shared basis

All three prompts solve the same task: translating the 155 restaurant questions from Task 2 into SQL. All three contain the same database schema and the same rules (which columns to return, how to tell a city from a region, what "best" means, how to ignore filler text). They differ only in the framework, so the comparison shows the effect of the framework, not of how much information each prompt got.

## P1 – RTF (Role, Task, Format)

Frompting describes RTF as *"the minimal AI-native framework"*, meant for quick structured prompts. My prompt has three parts:
- **Role:** an experienced database engineer;
- **Task:** the schema and the rules;
- **Format:** the exact form of the output CSV.

**Why I chose it:** it is the simplest framework that still has a structure, so it works well as a baseline. The model gets all the information it needs, but no extra help applying it. The Format part is also useful here, because the evaluator needs the output in an exact form.

**What I expect:** the fastest of the three. It might make mistakes on tricky questions (filler text, city vs. region), but since it has the same rules as the others, it could end up just as accurate.

## P2 – Few-Shot

Frompting describes Few-Shot as a framework that *"provides examples to guide AI output format and quality through pattern demonstration"*. On top of the rules, my prompt contains 8 solved question → SQL examples. Each one shows a different kind of question: a region, a street with filler text, "best", a name with an apostrophe, a question unrelated to restaurants, and so on. I wrote the examples myself; none of them comes from the test questions.

**Why I chose it:** a model copies a pattern from examples more reliably than it follows a written rule. In this task, a single small formatting mistake makes the whole answer wrong, so a stable output format really matters.

**What I expect:** high accuracy and very consistent SQL. The risk is that the model copies the examples too literally, for example adding a rating filter where there shouldn't be one.

## P3 – CoT (Chain of Thought)

Frompting describes CoT as a *"reasoning framework that breaks complex problems into sequential logical steps"*. In my prompt, the model goes through 6 steps for every question:
1. remove the filler text;
2. decide whether the location is a city or a region;
3. extract the values;
4. map them to columns;
5. write the SQL;
6. check it.

It records the results of these steps in a separate `analysis` column (city, food, rating, …). I deliberately gave it no examples, so that it tests step-by-step reasoning alone and doesn't overlap with P2.

**Why I chose it:** the hardest part of this dataset is understanding the question, not writing the SQL. Many questions contain irrelevant text, and "in the bay area" means something different from "in unknown". CoT makes the model deal with this before it writes anything. The saved analysis also helps explain errors later.

**What I expect:** the best handling of noisy questions, but clearly the slowest, because it has to write much more. If the rules already make the task easy, the extra steps may not help at all.

## Comparison

| | P1 RTF | P2 Few-Shot | P3 CoT |
|---|---|---|---|
| How it helps the model | structure | examples | step-by-step analysis |
| Expected accuracy | good | high | high |
| Expected speed | fast | fast | slowest |
| Main risk | tricky questions | copying examples too literally | slow, possibly unnecessary steps |

Each prompt tests a different way of helping the model: **structure**, **demonstration** and **reasoning**. That should make the differences in Task 2 easy to interpret.
