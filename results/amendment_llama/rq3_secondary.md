# RQ3: which signals predict escalation (secondary label)

6724 calls from 50 scenarios, 780 positive (11.6%).

## Predictive performance (leave-scenario-out)

- AUC 0.856 over 5 folds (per fold: 0.871, 0.892, 0.787, 0.880, 0.855)
- Brier score 0.083


### Calibration

| bin | mean_predicted | observed_rate | n |
|---|---|---|---|
| 0.000 | 0.006 | 0.002 | 3998.000 |
| 1.000 | 0.153 | 0.131 | 527.000 |
| 2.000 | 0.254 | 0.327 | 1046.000 |
| 3.000 | 0.337 | 0.298 | 916.000 |
| 4.000 | 0.431 | 0.370 | 235.000 |
| 5.000 | 0.574 | 0.000 | 1.000 |
| 6.000 | 0.613 | 0.000 | 1.000 |


## Overlapping features

| feature | vif |
|---|---|
| rolling_503_rate | 4.271 |
| retry_since_success | 4.345 |
| step_idx | 4.680 |
| reasoning_tokens_cum | 1.752 |
| surface_success | 2.079 |
| surface_service_unavailable | 5.824 |
| surface_blocked | 2.959 |


No feature set needed collapsing.


Constant, dropped: surface_tool_error.


## Importance (mean absolute SHAP, standardised features)

| rank | feature | coef | mean_abs_shap | imp_ci_low | imp_ci_high | rank_ci_low | rank_ci_high |
|---|---|---|---|---|---|---|---|
| 1 | surface_success | 2.666 | 2.332 | 2.215 | 2.489 | 1.000 | 2.000 |
| 2 | surface_service_unavailable | 2.701 | 2.212 | 1.970 | 2.456 | 1.000 | 2.000 |
| 3 | reasoning_tokens_cum | -1.132 | 0.741 | 0.470 | 1.097 | 3.000 | 4.000 |
| 4 | surface_blocked | -0.483 | 0.423 | 0.231 | 0.552 | 3.000 | 6.000 |
| 5 | retry_since_success | -0.444 | 0.324 | 0.028 | 0.660 | 4.000 | 7.000 |
| 6 | step_idx | -0.061 | 0.046 | 0.008 | 0.465 | 4.000 | 7.000 |
| 7 | rolling_503_rate | 0.048 | 0.040 | 0.003 | 0.199 | 5.000 | 7.000 |


Intervals: bootstrap over scenarios, 1000 replicates (0 skipped for a single label class).
