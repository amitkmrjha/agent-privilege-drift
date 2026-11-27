# RQ3: which signals predict escalation (secondary label)

8382 calls from 50 scenarios, 899 positive (10.7%).

## Predictive performance (leave-scenario-out)

- AUC 0.834 over 5 folds (per fold: 0.849, 0.866, 0.817, 0.839, 0.834)
- Brier score 0.082


### Calibration

| bin | mean_predicted | observed_rate | n |
|---|---|---|---|
| 0.000 | 0.009 | 0.011 | 4973.000 |
| 1.000 | 0.151 | 0.172 | 783.000 |
| 2.000 | 0.255 | 0.271 | 1866.000 |
| 3.000 | 0.326 | 0.269 | 654.000 |
| 4.000 | 0.440 | 0.337 | 83.000 |
| 5.000 | 0.535 | 0.043 | 23.000 |


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
| 1 | pc_collinear | 1.537 | 1.294 | 1.191 | 1.403 | 1.000 | 3.000 |
| 2 | surface_success | 1.559 | 1.264 | 1.127 | 1.407 | 1.000 | 3.000 |
| 3 | surface_blocked | -1.471 | 1.240 | 1.170 | 1.384 | 1.000 | 3.000 |
| 4 | reasoning_tokens_cum | -0.753 | 0.556 | 0.372 | 0.785 | 4.000 | 4.000 |
| 5 | retry_since_success | 0.335 | 0.248 | 0.102 | 0.416 | 5.000 | 5.000 |


Intervals: bootstrap over scenarios, 1000 replicates (0 skipped for a single label class).
