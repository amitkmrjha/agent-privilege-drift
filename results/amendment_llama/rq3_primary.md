# RQ3: which signals predict escalation (primary label)

6724 calls from 50 scenarios, 2498 positive (37.2%).

## Predictive performance (leave-scenario-out)

- AUC 0.759 over 5 folds (per fold: 0.768, 0.743, 0.826, 0.729, 0.767)
- Brier score 0.187


### Calibration

| bin | mean_predicted | observed_rate | n |
|---|---|---|---|
| 0.000 | 0.074 | 0.097 | 1510.000 |
| 1.000 | 0.121 | 0.012 | 418.000 |
| 2.000 | 0.271 | 0.262 | 271.000 |
| 3.000 | 0.347 | 0.358 | 1582.000 |
| 4.000 | 0.444 | 0.467 | 949.000 |
| 5.000 | 0.554 | 0.595 | 496.000 |
| 6.000 | 0.650 | 0.636 | 1055.000 |
| 7.000 | 0.738 | 0.632 | 364.000 |
| 8.000 | 0.839 | 0.870 | 69.000 |
| 9.000 | 0.920 | 1.000 | 10.000 |


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
| 1 | surface_blocked | 1.148 | 1.006 | 0.751 | 1.336 | 1.000 | 1.000 |
| 2 | surface_service_unavailable | 0.786 | 0.644 | 0.435 | 0.946 | 2.000 | 5.000 |
| 3 | surface_success | 0.692 | 0.605 | 0.378 | 0.927 | 2.000 | 5.000 |
| 4 | reasoning_tokens_cum | -0.718 | 0.470 | 0.280 | 0.708 | 2.000 | 5.000 |
| 5 | step_idx | 0.540 | 0.405 | 0.164 | 0.684 | 2.000 | 6.000 |
| 6 | retry_since_success | 0.199 | 0.145 | 0.008 | 0.305 | 5.000 | 7.000 |
| 7 | rolling_503_rate | -0.026 | 0.021 | 0.002 | 0.160 | 6.000 | 7.000 |


Intervals: bootstrap over scenarios, 1000 replicates (0 skipped for a single label class).
