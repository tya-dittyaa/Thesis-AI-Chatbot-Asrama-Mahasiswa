# Fair rerun patch (Scenarios 2–4)

These files replace the matching files under `code/pipeline/`. `fair-rerun.diff` shows every change.

What changed:
1. **No label leakage.** The portal fields `InitialDepartmentName` and `SubjectCategory` are no longer sent to any LLM (S2, S3, Agent 1, Agent 2). In the benchmark, the portal department equals the label in 499 of 500 tickets.
2. **Equal prompts.** S2 and S3 now use the same 26-subcategory directory and the same content rules as Agent 2. The "Prior Anchoring" rule, which said to keep the portal department, is removed everywhere.
3. **Confidence for the hybrid.** S2 and S3 now output `confidence_score`, which is saved as `ConfidenceScore`.
4. **The policy reaches Agent 2.** The main MAS run now passes Agent 1's `extracted_handbook_policy` to Agent 2. Before this change, only the retry script did that.
5. **No selective retry.** `retry_failed_mas_tickets.py` now retries only API or quota failures by default. Do not use `--upgrade-recheck` for results you report.
6. **Fair hybrid gate.** The gate escalates when S2 predicts Finance or its confidence is below `theta`, and it no longer uses the portal department. Escalated tickets are charged the latency and tokens of both S2 and S4. Choose `theta` on a dev set taken from `train_pool.csv`, not on the benchmark.

How to rerun:
- Run S2, S3 and S4 once each, on all 500 tickets, with the same model ID. Delete the old `*_predictions.csv` files first so nothing is reused.
- Then run `compare_results.py`.
- Write down the model ID and the run dates for the paper.

Not tested here: these scripts need your Gemini API keys, so I only checked that they compile.
