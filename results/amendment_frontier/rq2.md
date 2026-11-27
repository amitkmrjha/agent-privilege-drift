# RQ2: IBAC against MAC and no mediator

## Rates by cell (mean over scenarios, bootstrap interval)

| metric | model | p | mediator | n_scenarios | mean | ci_low | ci_high |
|---|---|---|---|---|---|---|---|
| blocked_rate | frontier | 0.000 | ibac | 50 | 0.017 | 0.000 | 0.043 |
| blocked_rate | frontier | 0.000 | mac | 50 | 0.021 | 0.000 | 0.051 |
| blocked_rate | frontier | 0.000 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier | 0.300 | ibac | 50 | 0.040 | 0.017 | 0.067 |
| blocked_rate | frontier | 0.300 | mac | 50 | 0.016 | 0.000 | 0.038 |
| blocked_rate | frontier | 0.300 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier | 0.600 | ibac | 50 | 0.105 | 0.069 | 0.144 |
| blocked_rate | frontier | 0.600 | mac | 50 | 0.127 | 0.092 | 0.164 |
| blocked_rate | frontier | 0.600 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.000 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.000 | mac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.000 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.300 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.300 | mac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.300 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.600 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.600 | mac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.600 | none | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.000 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.000 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.000 | none | 50 | 0.023 | 0.000 | 0.057 |
| executed_violation_rate | frontier | 0.300 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.300 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.300 | none | 50 | 0.040 | 0.008 | 0.086 |
| executed_violation_rate | frontier | 0.600 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.600 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.600 | none | 50 | 0.104 | 0.074 | 0.137 |
| executed_violation_rate | frontier_large | 0.000 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.000 | mac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.000 | none | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.300 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.300 | mac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.300 | none | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.600 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.600 | mac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.600 | none | 50 | 0.004 | 0.000 | 0.011 |
| proposed_violation_rate | frontier | 0.000 | ibac | 50 | 0.017 | 0.000 | 0.043 |
| proposed_violation_rate | frontier | 0.000 | mac | 50 | 0.021 | 0.000 | 0.051 |
| proposed_violation_rate | frontier | 0.000 | none | 50 | 0.023 | 0.000 | 0.057 |
| proposed_violation_rate | frontier | 0.300 | ibac | 50 | 0.040 | 0.017 | 0.067 |
| proposed_violation_rate | frontier | 0.300 | mac | 50 | 0.016 | 0.000 | 0.038 |
| proposed_violation_rate | frontier | 0.300 | none | 50 | 0.040 | 0.008 | 0.086 |
| proposed_violation_rate | frontier | 0.600 | ibac | 50 | 0.105 | 0.069 | 0.144 |
| proposed_violation_rate | frontier | 0.600 | mac | 50 | 0.127 | 0.092 | 0.164 |
| proposed_violation_rate | frontier | 0.600 | none | 50 | 0.104 | 0.074 | 0.137 |
| proposed_violation_rate | frontier_large | 0.000 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.000 | mac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.000 | none | 50 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.300 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.300 | mac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.300 | none | 50 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.600 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.600 | mac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.600 | none | 50 | 0.004 | 0.000 | 0.011 |
| task_success | frontier | 0.000 | ibac | 50 | 1.000 | 1.000 | 1.000 |
| task_success | frontier | 0.000 | mac | 50 | 1.000 | 1.000 | 1.000 |
| task_success | frontier | 0.000 | none | 50 | 1.000 | 1.000 | 1.000 |
| task_success | frontier | 0.300 | ibac | 50 | 0.960 | 0.927 | 0.987 |
| task_success | frontier | 0.300 | mac | 50 | 1.000 | 1.000 | 1.000 |
| task_success | frontier | 0.300 | none | 50 | 0.993 | 0.980 | 1.000 |
| task_success | frontier | 0.600 | ibac | 50 | 0.840 | 0.780 | 0.900 |
| task_success | frontier | 0.600 | mac | 50 | 0.773 | 0.707 | 0.840 |
| task_success | frontier | 0.600 | none | 50 | 0.913 | 0.873 | 0.953 |
| task_success | frontier_large | 0.000 | ibac | 1 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.000 | mac | 1 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.000 | none | 50 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.300 | ibac | 1 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.300 | mac | 1 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.300 | none | 50 | 0.967 | 0.940 | 0.993 |
| task_success | frontier_large | 0.600 | ibac | 1 | 0.667 | 0.667 | 0.667 |
| task_success | frontier_large | 0.600 | mac | 1 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.600 | none | 50 | 0.853 | 0.793 | 0.907 |


## Utility floor

Difference in task success, IBAC minus the comparator, with a bootstrap interval; the floor is 5 points.


| model | p | comparator | n | n_excluded | diff | ci_low | ci_high | outcome |
|---|---|---|---|---|---|---|---|---|
| frontier | 0 | mac | 50 | 0 | 0.000 | 0.000 | 0.000 | met |
| frontier | 0 | none | 50 | 0 | 0.000 | 0.000 | 0.000 | met |
| frontier | 0.3 | mac | 50 | 0 | -0.040 | -0.073 | -0.013 | inconclusive |
| frontier | 0.3 | none | 50 | 0 | -0.033 | -0.067 | 0.000 | inconclusive |
| frontier | 0.6 | mac | 50 | 0 | 0.067 | -0.027 | 0.160 | met |
| frontier | 0.6 | none | 50 | 0 | -0.073 | -0.147 | 0.000 | inconclusive |
| frontier | all | mac | 50 | 0 | 0.009 | -0.024 | 0.042 | met |
| frontier | all | none | 50 | 0 | -0.036 | -0.064 | -0.007 | inconclusive |
| frontier_large | 0 | mac | 1 | 49 | 0.000 | 0.000 | 0.000 | met |
| frontier_large | 0 | none | 1 | 49 | 0.000 | 0.000 | 0.000 | met |
| frontier_large | 0.3 | mac | 1 | 49 | 0.000 | 0.000 | 0.000 | met |
| frontier_large | 0.3 | none | 1 | 49 | 0.000 | 0.000 | 0.000 | met |
| frontier_large | 0.6 | mac | 1 | 49 | -0.333 | -0.333 | -0.333 | not_met |
| frontier_large | 0.6 | none | 1 | 49 | -0.333 | -0.333 | -0.333 | not_met |
| frontier_large | all | mac | 1 | 49 | -0.111 | -0.111 | -0.111 | not_met |
| frontier_large | all | none | 1 | 49 | -0.111 | -0.111 | -0.111 | not_met |


Pooled over the failure rates:

- frontier, against mac: **met**. IBAC's task success is not more than 5 points below mac's.

- frontier, against none: **inconclusive**. The data neither show IBAC within 5 points of none nor more than 5 points below it.

- frontier_large, against mac: **not_met**. IBAC's task success is more than 5 points below mac's.

- frontier_large, against none: **not_met**. IBAC's task success is more than 5 points below none's.


## Mediator contrasts (Holm within each metric)

| metric | model | p | mediator_a | mediator_b | n | n_excluded | diff | p_wilcoxon | p_holm | reject_holm | cliffs_delta | magnitude | cohens_dz |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proposed_violation_rate | frontier | 0.000 | ibac | mac | 50 | 0 | -0.004 | 0.180 | 1.000 | False | -0.020 | negligible | -0.180 |
| proposed_violation_rate | frontier | 0.000 | ibac | none | 50 | 0 | -0.007 | 0.180 | 1.000 | False | -0.020 | negligible | -0.202 |
| proposed_violation_rate | frontier | 0.000 | mac | none | 50 | 0 | -0.002 | 0.317 | 1.000 | False | -0.000 | negligible | -0.141 |
| proposed_violation_rate | frontier | 0.300 | ibac | mac | 50 | 0 | 0.023 | 0.007 | 0.132 | False | 0.137 | negligible | 0.392 |
| proposed_violation_rate | frontier | 0.300 | ibac | none | 50 | 0 | -0.001 | 0.724 | 1.000 | False | 0.068 | negligible | -0.009 |
| proposed_violation_rate | frontier | 0.300 | mac | none | 50 | 0 | -0.024 | 0.068 | 1.000 | False | -0.077 | negligible | -0.279 |
| proposed_violation_rate | frontier | 0.600 | ibac | mac | 50 | 0 | -0.022 | 0.654 | 1.000 | False | -0.112 | negligible | -0.122 |
| proposed_violation_rate | frontier | 0.600 | ibac | none | 50 | 0 | 0.001 | 0.862 | 1.000 | False | -0.043 | negligible | 0.006 |
| proposed_violation_rate | frontier | 0.600 | mac | none | 50 | 0 | 0.023 | 0.267 | 1.000 | False | 0.079 | negligible | 0.159 |
| proposed_violation_rate | frontier_large | 0.000 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.000 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.000 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.300 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.300 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.300 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.600 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.600 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.600 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier | 0.000 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | frontier | 0.000 | ibac | none | 50 | 0 | -0.023 | 0.109 | 1.000 | False | -0.060 | negligible | -0.219 |
| executed_violation_rate | frontier | 0.000 | mac | none | 50 | 0 | -0.023 | 0.109 | 1.000 | False | -0.060 | negligible | -0.219 |
| executed_violation_rate | frontier | 0.300 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | frontier | 0.300 | ibac | none | 50 | 0 | -0.040 | 0.018 | 0.284 | False | -0.140 | negligible | -0.278 |
| executed_violation_rate | frontier | 0.300 | mac | none | 50 | 0 | -0.040 | 0.018 | 0.284 | False | -0.140 | negligible | -0.278 |
| executed_violation_rate | frontier | 0.600 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | frontier | 0.600 | ibac | none | 50 | 0 | -0.104 | 0.000 | 0.000 | True | -0.580 | large | -0.913 |
| executed_violation_rate | frontier | 0.600 | mac | none | 50 | 0 | -0.104 | 0.000 | 0.000 | True | -0.580 | large | -0.913 |
| executed_violation_rate | frontier_large | 0.000 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.000 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.000 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.300 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.300 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.300 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.600 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.600 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.600 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier | 0.000 | ibac | mac | 50 | 0 | -0.004 | 0.180 | 1.000 | False | -0.020 | negligible | -0.180 |
| blocked_rate | frontier | 0.000 | ibac | none | 50 | 0 | 0.017 | 0.180 | 1.000 | False | 0.040 | negligible | 0.198 |
| blocked_rate | frontier | 0.000 | mac | none | 50 | 0 | 0.021 | 0.109 | 1.000 | False | 0.060 | negligible | 0.227 |
| blocked_rate | frontier | 0.300 | ibac | mac | 50 | 0 | 0.023 | 0.007 | 0.110 | False | 0.137 | negligible | 0.392 |
| blocked_rate | frontier | 0.300 | ibac | none | 50 | 0 | 0.040 | 0.003 | 0.048 | True | 0.200 | small | 0.430 |
| blocked_rate | frontier | 0.300 | mac | none | 50 | 0 | 0.016 | 0.109 | 1.000 | False | 0.060 | negligible | 0.225 |
| blocked_rate | frontier | 0.600 | ibac | mac | 50 | 0 | -0.022 | 0.654 | 1.000 | False | -0.112 | negligible | -0.122 |
| blocked_rate | frontier | 0.600 | ibac | none | 50 | 0 | 0.105 | 0.000 | 0.000 | True | 0.460 | medium | 0.764 |
| blocked_rate | frontier | 0.600 | mac | none | 50 | 0 | 0.127 | 0.000 | 0.000 | True | 0.640 | large | 0.972 |
| blocked_rate | frontier_large | 0.000 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.000 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.000 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.300 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.300 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.300 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.600 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.600 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.600 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier | 0.000 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | frontier | 0.000 | ibac | none | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | frontier | 0.000 | mac | none | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | frontier | 0.300 | ibac | mac | 50 | 0 | -0.040 | 0.014 | 0.243 | False | -0.120 | negligible | -0.366 |
| task_success | frontier | 0.300 | ibac | none | 50 | 0 | -0.033 | 0.059 | 0.941 | False | -0.100 | negligible | -0.275 |
| task_success | frontier | 0.300 | mac | none | 50 | 0 | 0.007 | 0.317 | 1.000 | False | 0.020 | negligible | 0.141 |
| task_success | frontier | 0.600 | ibac | mac | 50 | 0 | 0.067 | 0.101 | 1.000 | False | 0.146 | negligible | 0.198 |
| task_success | frontier | 0.600 | ibac | none | 50 | 0 | -0.073 | 0.084 | 1.000 | False | -0.161 | small | -0.270 |
| task_success | frontier | 0.600 | mac | none | 50 | 0 | -0.140 | 0.001 | 0.020 | True | -0.311 | small | -0.554 |
| task_success | frontier_large | 0.000 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.000 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.000 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.300 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.300 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.300 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.600 | ibac | mac | 1 | 49 | -0.333 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| task_success | frontier_large | 0.600 | ibac | none | 1 | 49 | -0.333 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| task_success | frontier_large | 0.600 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |


## IBAC classifier

| model | p | runs | failed_runs | failure_rate |
|---|---|---|---|---|
| frontier | 0.000 | 150 | 0 | 0.000 |
| frontier | 0.300 | 150 | 0 | 0.000 |
| frontier | 0.600 | 150 | 0 | 0.000 |
| frontier_large | 0.000 | 3 | 0 | 0.000 |
| frontier_large | 0.300 | 3 | 0 | 0.000 |
| frontier_large | 0.600 | 3 | 0 | 0.000 |


Accuracy against the benchmark's domain label: 42 of 50 scenarios (0.840), 0 unreadable.
