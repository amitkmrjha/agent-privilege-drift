# RQ1: failure pressure and escalation

## Violation rate by cell

| mediator | model | p | n_scenarios | mean | ci_low | ci_high |
|---|---|---|---|---|---|---|
| ibac | frontier | 0.000 | 50 | 0.017 | 0.000 | 0.043 |
| ibac | frontier | 0.300 | 50 | 0.040 | 0.017 | 0.067 |
| ibac | frontier | 0.600 | 50 | 0.105 | 0.069 | 0.144 |
| ibac | frontier_large | 0.000 | 1 | 0.000 | 0.000 | 0.000 |
| ibac | frontier_large | 0.300 | 1 | 0.000 | 0.000 | 0.000 |
| ibac | frontier_large | 0.600 | 1 | 0.000 | 0.000 | 0.000 |
| mac | frontier | 0.000 | 50 | 0.021 | 0.000 | 0.051 |
| mac | frontier | 0.300 | 50 | 0.016 | 0.000 | 0.038 |
| mac | frontier | 0.600 | 50 | 0.127 | 0.092 | 0.164 |
| mac | frontier_large | 0.000 | 1 | 0.000 | 0.000 | 0.000 |
| mac | frontier_large | 0.300 | 1 | 0.000 | 0.000 | 0.000 |
| mac | frontier_large | 0.600 | 1 | 0.000 | 0.000 | 0.000 |
| none | frontier | 0.000 | 50 | 0.023 | 0.000 | 0.057 |
| none | frontier | 0.300 | 50 | 0.040 | 0.008 | 0.086 |
| none | frontier | 0.600 | 50 | 0.104 | 0.074 | 0.137 |
| none | frontier_large | 0.000 | 50 | 0.000 | 0.000 | 0.000 |
| none | frontier_large | 0.300 | 50 | 0.000 | 0.000 | 0.000 |
| none | frontier_large | 0.600 | 50 | 0.004 | 0.000 | 0.011 |

## Primary contrast

Failure rate 0 to 0.6, mediator `none`, 50 scenarios (0 excluded for missing values).

- frontier delta: 0.081; frontier_large delta: 0.004
- Difference in differences (frontier_large minus frontier): **-0.077**, 95% bootstrap interval [-0.103, -0.050]
- Paired Wilcoxon p = 0.0000; Cliff's delta = -0.514 (large); Cohen's dz = -0.801


The interval lies inside +/-0.12: the data rule out a difference as large as the 12%-point target, and any real difference is at most 0.103 (an upper bound, not an estimate).


## Contrasts (Holm within each kind)

| kind | mediator | model_a | p_a | model_b | p_b | n | n_excluded | diff | p_wilcoxon | p_holm | reject_holm | cliffs_delta | magnitude | cohens_dz |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| across_p | ibac | frontier | 0.300 | frontier | 0.000 | 50 | 0 | 0.023 | 0.029 | 0.333 | False | 0.153 | small | 0.344 |
| across_p | ibac | frontier | 0.600 | frontier | 0.000 | 50 | 0 | 0.089 | 0.000 | 0.000 | True | 0.406 | medium | 0.743 |
| across_p | ibac | frontier | 0.600 | frontier | 0.300 | 50 | 0 | 0.066 | 0.001 | 0.018 | True | 0.275 | small | 0.530 |
| across_p | mac | frontier | 0.300 | frontier | 0.000 | 50 | 0 | -0.005 | 0.465 | 1.000 | False | -0.001 | negligible | -0.129 |
| across_p | mac | frontier | 0.600 | frontier | 0.000 | 50 | 0 | 0.106 | 0.000 | 0.001 | True | 0.556 | large | 0.739 |
| across_p | mac | frontier | 0.600 | frontier | 0.300 | 50 | 0 | 0.111 | 0.000 | 0.000 | True | 0.568 | large | 0.806 |
| across_p | none | frontier | 0.300 | frontier | 0.000 | 50 | 0 | 0.017 | 0.028 | 0.333 | False | 0.076 | negligible | 0.289 |
| across_p | none | frontier | 0.600 | frontier | 0.000 | 50 | 0 | 0.081 | 0.000 | 0.001 | True | 0.497 | large | 0.848 |
| across_p | none | frontier | 0.600 | frontier | 0.300 | 50 | 0 | 0.064 | 0.001 | 0.013 | True | 0.446 | medium | 0.532 |
| across_p | ibac | frontier_large | 0.300 | frontier_large | 0.000 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | ibac | frontier_large | 0.600 | frontier_large | 0.000 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | ibac | frontier_large | 0.600 | frontier_large | 0.300 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | mac | frontier_large | 0.300 | frontier_large | 0.000 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | mac | frontier_large | 0.600 | frontier_large | 0.000 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | mac | frontier_large | 0.600 | frontier_large | 0.300 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | none | frontier_large | 0.300 | frontier_large | 0.000 | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| across_p | none | frontier_large | 0.600 | frontier_large | 0.000 | 50 | 0 | 0.004 | 0.180 | 1.000 | False | 0.040 | negligible | 0.197 |
| across_p | none | frontier_large | 0.600 | frontier_large | 0.300 | 50 | 0 | 0.004 | 0.180 | 1.000 | False | 0.040 | negligible | 0.197 |
| between_models | ibac | frontier_large | 0.000 | frontier | 0.000 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| between_models | mac | frontier_large | 0.000 | frontier | 0.000 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| between_models | none | frontier_large | 0.000 | frontier | 0.000 | 50 | 0 | -0.023 | 0.109 | 0.762 | False | -0.060 | negligible | -0.219 |
| between_models | ibac | frontier_large | 0.300 | frontier | 0.300 | 1 | 49 | -0.167 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| between_models | mac | frontier_large | 0.300 | frontier | 0.300 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| between_models | none | frontier_large | 0.300 | frontier | 0.300 | 50 | 0 | -0.040 | 0.018 | 0.142 | False | -0.140 | negligible | -0.278 |
| between_models | ibac | frontier_large | 0.600 | frontier | 0.600 | 1 | 49 | -0.333 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| between_models | mac | frontier_large | 0.600 | frontier | 0.600 | 1 | 49 | -0.167 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| between_models | none | frontier_large | 0.600 | frontier | 0.600 | 50 | 0 | -0.100 | 0.000 | 0.000 | True | -0.554 | large | -0.933 |


## Page's trend across failure rates

| model | mediator | n | k | L | p_value |
|---|---|---|---|---|---|
| frontier | ibac | 50 | 3 | 634.500 | 0.000 |
| frontier | mac | 50 | 3 | 640.500 | 0.000 |
| frontier | none | 50 | 3 | 639.500 | 0.000 |
| frontier_large | none | 50 | 3 | 603.000 | 0.382 |
