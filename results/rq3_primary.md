# RQ3: which signals predict escalation (primary label)

8382 calls from 50 scenarios, 2840 positive (33.9%).

## Predictive performance (leave-scenario-out)

- AUC 0.768 over 5 folds (per fold: 0.790, 0.783, 0.782, 0.762, 0.774)
- Brier score 0.175


### Calibration

| bin | mean_predicted | observed_rate | n |
|---|---|---|---|
| 0.000 | 0.079 | 0.070 | 2700.000 |
| 1.000 | 0.200 | 0.000 | 1.000 |
| 2.000 | 0.270 | 0.420 | 469.000 |
| 3.000 | 0.345 | 0.307 | 2582.000 |
| 4.000 | 0.440 | 0.532 | 592.000 |
| 5.000 | 0.549 | 0.617 | 711.000 |
| 6.000 | 0.655 | 0.584 | 522.000 |
| 7.000 | 0.750 | 0.726 | 603.000 |
| 8.000 | 0.839 | 0.807 | 176.000 |
| 9.000 | 0.920 | 0.923 | 26.000 |


## Overlapping features

| feature | vif |
|---|---|
| rolling_503_rate | 5.231 |
| retry_since_success | 4.790 |
| step_idx | 7.495 |
| reasoning_tokens_cum | 4.265 |
| surface_success | 1.945 |
| surface_service_unavailable | 6.850 |
| surface_blocked | 2.963 |


Replaced by `pc_collinear` (keeps 64.1% of their variance): rolling_503_rate, step_idx, surface_service_unavailable.


Constant, dropped: surface_tool_error.


## Importance (mean absolute SHAP, standardised features)

| rank | feature | coef | mean_abs_shap | imp_ci_low | imp_ci_high | rank_ci_low | rank_ci_high |
|---|---|---|---|---|---|---|---|
| 1 | surface_blocked | 1.000 | 0.843 | 0.663 | 1.023 | 1.000 | 1.000 |
| 2 | surface_success | 0.716 | 0.580 | 0.436 | 0.757 | 2.000 | 3.000 |
| 3 | pc_collinear | 0.658 | 0.554 | 0.392 | 0.758 | 2.000 | 4.000 |
| 4 | retry_since_success | 0.445 | 0.329 | 0.173 | 0.482 | 3.000 | 4.000 |
| 5 | reasoning_tokens_cum | -0.158 | 0.117 | 0.019 | 0.213 | 5.000 | 5.000 |


Intervals: bootstrap over scenarios, 1000 replicates (0 skipped for a single label class).
