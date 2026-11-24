# Assessment by laguna-s-2.1

# Week 03 Prompting
- Awarded: 5b out of 5b
- Commentary: All four tasks are complete and high-quality. The student chose three prompting frameworks (RTF, Few-Shot, CoT) from frompting.com, solved 155 restaurant text-to-SQL questions with each in fresh sessions, measured inference times, proposed an original metric (Correct-Answer Throughput), and re-ran the comparison on two models with proper statistical tests. Every figure in the reports matches the underlying CSV/JSON data and the prediction files; the SQL never errored and all three prompts reached 154/155. The visualizations (comparison.png, cat.png, time_by_run.png, cat_by_prompt.png) could not be viewed as images by this model, but their content is fully recoverable from the accompanying results CSVs and plotting scripts and is consistent with the reports.

## Task 1
- Awarded: 1b   (max 1b)
- Commentary: Three distinct frameworks chosen (RTF, Few-Shot, CoT) from frompting.com/frameworks, explicitly avoiding ROSES and zero-shot as required. Each framework is realized as a complete, self-contained prompt file (prompts/P1_RTF.md, prompts/P2_FewShot.md, prompts/P3_CoT.md) and catalogued in prompts.json with IDs, sources, and file paths. The REPORT explains why each framework was chosen and what it is expected to do, and notes that all three share the same schema/rules so the comparison isolates the framework. This fully satisfies the "data file + report on why each was chosen and where found" output.

## Task 2
- Awarded: 1b   (max 1b)
- Commentary: The three Task 1 prompts were used to translate all 155 questions into SQL, with each prompt run in a new session. Predictions are stored as CSV files with prompt/model/framework metadata (.run_*.json), inference time was measured, and evaluate_all.py scores them by multiset comparison of executed rows. The REPORT compares accuracy and time and embeds a visualization (results/comparison.png). Reported numbers (154/155, 0.9935 accuracy; 224.7/221.0/278.7s) match results/summary.csv and the per-question all_predictions.csv exactly. Full completion.

## Task 3
- Awarded: 1b   (max 1b)
- Commentary: An original metric, Correct-Answer Throughput (CAT = sum of row-level F1 over 155 questions / inference time in minutes), is proposed, defended, and shown to complement (not replace) exact match by rewarding partial credit and penalizing slow prompts. metric.py implements F1 over predicted-vs-expected row multisets and CAT; per_question_f1.csv and metric_summary.csv hold the outputs, with cat.png visualizing them. Reported values (41.12 / 41.81 / 33.15) match the CSVs, and the analysis honestly notes that partial credit had nothing to reward here because the single wrong answer was completely wrong. Complete and well argued.

## Task 4
- Awarded: 2b   (max 2b)
- Commentary: The comparison is repeated (Opus x3, Haiku x1 per prompt) with every run in a new session. analysis.py produces results/runs.csv, summary.csv, stat_tests.csv, sql_consistency.csv and the two charts. Statistical significance is addressed directly: Cochran's Q and exact McNemar tests give p = 1 for accuracy (no difference), while time differences are tested with one-way ANOVA, Kruskal-Wallis, and Holm-corrected Welch t-tests. The report correctly identifies the CoT slowness as significant (p ~ 0.003, ~25% slower) and treats the agent-induced 549s outlier transparently. The "Why?" section discusses prompts, model, and coding agent as separate factors, supported by sql_consistency.csv (Few-Shot and CoT produce byte-identical queries across runs; RTF varies only condition order). All reported times and CAT values match the CSVs. The only minor narrative gloss is saying "the t-tests are not significant (p = 0.48)" when describing all-runs results, whereas the P1-vs-P2 Welch t-test is in fact significant (0.0233); this does not affect the sound conclusions. Full credit warranted.
