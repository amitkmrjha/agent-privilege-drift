# RQ3: which signals predict escalation (secondary label)

2996 calls from 50 scenarios, 123 positive (4.1%).

## Predictive performance (leave-scenario-out)

- AUC 0.947 over 5 folds (per fold: 0.981, 0.980, 0.968, 0.986, 0.915)
- Brier score 0.033


### Calibration

| bin | mean_predicted | observed_rate | n |
|---|---|---|---|
| 0.000 | 0.012 | 0.005 | 2616.000 |
| 1.000 | 0.125 | 0.032 | 217.000 |
| 2.000 | 0.261 | 0.894 | 85.000 |
| 3.000 | 0.318 | 0.900 | 30.000 |
| 4.000 | 0.459 | 0.091 | 11.000 |
| 5.000 | 0.549 | 0.000 | 14.000 |
| 6.000 | 0.651 | 0.000 | 5.000 |
| 7.000 | 0.755 | 0.000 | 8.000 |
| 8.000 | 0.848 | 0.000 | 6.000 |
| 9.000 | 0.963 | 0.000 | 4.000 |


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
| 1 | pc_collinear | 2.585 | 2.422 | 1.999 | 3.345 | 1.000 | 1.000 |
| 2 | surface_blocked | -1.126 | 0.555 | 0.438 | 0.695 | 2.000 | 2.000 |
| 3 | reasoning_tokens_cum | -0.303 | 0.196 | 0.053 | 0.536 | 3.000 | 3.000 |
| 4 | surface_success | 0.262 | 0.023 | 0.000 | 0.061 | 4.000 | 4.000 |


Intervals: bootstrap over scenarios, 1000 replicates (0 skipped for a single label class).
