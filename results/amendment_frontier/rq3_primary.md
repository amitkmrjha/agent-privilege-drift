# RQ3: which signals predict escalation (primary label)

2996 calls from 50 scenarios, 348 positive (11.6%).

## Predictive performance (leave-scenario-out)

- AUC 0.875 over 5 folds (per fold: 0.989, 0.754, 0.886, 0.993, 0.944)
- Brier score 0.052


### Calibration

| bin | mean_predicted | observed_rate | n |
|---|---|---|---|
| 0.000 | 0.013 | 0.025 | 1972.000 |
| 1.000 | 0.130 | 0.022 | 489.000 |
| 2.000 | 0.219 | 0.024 | 207.000 |
| 3.000 | 0.353 | 0.929 | 99.000 |
| 4.000 | 0.446 | 0.815 | 27.000 |
| 5.000 | 0.527 | 0.833 | 18.000 |
| 6.000 | 0.663 | 0.850 | 20.000 |
| 7.000 | 0.776 | 0.867 | 45.000 |
| 8.000 | 0.844 | 0.858 | 113.000 |
| 9.000 | 0.920 | 0.167 | 6.000 |


## Overlapping features

| feature | vif |
|---|---|
| rolling_503_rate | 32.500 |
| retry_since_success | 261.147 |
| step_idx | 259.479 |
| reasoning_tokens_cum | 1.188 |
| surface_success | 2.163 |
| surface_service_unavailable | 35.989 |
| surface_blocked | 4.661 |


Replaced by `pc_collinear` (keeps 75.8% of their variance): rolling_503_rate, retry_since_success, step_idx, surface_service_unavailable.


Constant, dropped: surface_tool_error.


## Importance (mean absolute SHAP, standardised features)

| rank | feature | coef | mean_abs_shap | imp_ci_low | imp_ci_high | rank_ci_low | rank_ci_high |
|---|---|---|---|---|---|---|---|
| 1 | pc_collinear | 1.770 | 1.658 | 0.939 | 5.146 | 1.000 | 1.000 |
| 2 | surface_blocked | 0.650 | 0.321 | 0.255 | 0.397 | 2.000 | 3.000 |
| 3 | reasoning_tokens_cum | -0.127 | 0.082 | 0.005 | 0.620 | 2.000 | 4.000 |
| 4 | surface_success | 0.253 | 0.023 | 0.000 | 0.083 | 3.000 | 4.000 |


Intervals: bootstrap over scenarios, 1000 replicates (0 skipped for a single label class).
