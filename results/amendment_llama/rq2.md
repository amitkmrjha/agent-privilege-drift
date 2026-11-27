# RQ2: IBAC against MAC and no mediator

## Rates by cell (mean over scenarios, bootstrap interval)

| metric | model | p | mediator | n_scenarios | mean | ci_low | ci_high |
|---|---|---|---|---|---|---|---|
| blocked_rate | frontier_large | 0.000 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.000 | mac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.000 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.300 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.300 | mac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.300 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.600 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.600 | mac | 1 | 0.000 | 0.000 | 0.000 |
| blocked_rate | frontier_large | 0.600 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | llama | 0.000 | ibac | 50 | 0.305 | 0.242 | 0.368 |
| blocked_rate | llama | 0.000 | mac | 50 | 0.301 | 0.245 | 0.356 |
| blocked_rate | llama | 0.000 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | llama | 0.300 | ibac | 50 | 0.353 | 0.299 | 0.407 |
| blocked_rate | llama | 0.300 | mac | 50 | 0.332 | 0.282 | 0.383 |
| blocked_rate | llama | 0.300 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | llama | 0.600 | ibac | 50 | 0.391 | 0.348 | 0.433 |
| blocked_rate | llama | 0.600 | mac | 50 | 0.394 | 0.346 | 0.440 |
| blocked_rate | llama | 0.600 | none | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.000 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.000 | mac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.000 | none | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.300 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.300 | mac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.300 | none | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.600 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.600 | mac | 1 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier_large | 0.600 | none | 50 | 0.004 | 0.000 | 0.011 |
| executed_violation_rate | llama | 0.000 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.000 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.000 | none | 50 | 0.308 | 0.244 | 0.371 |
| executed_violation_rate | llama | 0.300 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.300 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.300 | none | 50 | 0.308 | 0.250 | 0.365 |
| executed_violation_rate | llama | 0.600 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.600 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.600 | none | 50 | 0.379 | 0.331 | 0.427 |
| proposed_violation_rate | frontier_large | 0.000 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.000 | mac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.000 | none | 50 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.300 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.300 | mac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.300 | none | 50 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.600 | ibac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.600 | mac | 1 | 0.000 | 0.000 | 0.000 |
| proposed_violation_rate | frontier_large | 0.600 | none | 50 | 0.004 | 0.000 | 0.011 |
| proposed_violation_rate | llama | 0.000 | ibac | 50 | 0.305 | 0.242 | 0.368 |
| proposed_violation_rate | llama | 0.000 | mac | 50 | 0.301 | 0.245 | 0.356 |
| proposed_violation_rate | llama | 0.000 | none | 50 | 0.308 | 0.244 | 0.371 |
| proposed_violation_rate | llama | 0.300 | ibac | 50 | 0.353 | 0.299 | 0.407 |
| proposed_violation_rate | llama | 0.300 | mac | 50 | 0.332 | 0.282 | 0.383 |
| proposed_violation_rate | llama | 0.300 | none | 50 | 0.308 | 0.250 | 0.365 |
| proposed_violation_rate | llama | 0.600 | ibac | 50 | 0.391 | 0.348 | 0.433 |
| proposed_violation_rate | llama | 0.600 | mac | 50 | 0.394 | 0.346 | 0.440 |
| proposed_violation_rate | llama | 0.600 | none | 50 | 0.379 | 0.331 | 0.427 |
| task_success | frontier_large | 0.000 | ibac | 1 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.000 | mac | 1 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.000 | none | 50 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.300 | ibac | 1 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.300 | mac | 1 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.300 | none | 50 | 0.967 | 0.940 | 0.993 |
| task_success | frontier_large | 0.600 | ibac | 1 | 0.667 | 0.667 | 0.667 |
| task_success | frontier_large | 0.600 | mac | 1 | 1.000 | 1.000 | 1.000 |
| task_success | frontier_large | 0.600 | none | 50 | 0.853 | 0.793 | 0.907 |
| task_success | llama | 0.000 | ibac | 50 | 1.000 | 1.000 | 1.000 |
| task_success | llama | 0.000 | mac | 50 | 1.000 | 1.000 | 1.000 |
| task_success | llama | 0.000 | none | 50 | 1.000 | 1.000 | 1.000 |
| task_success | llama | 0.300 | ibac | 50 | 1.000 | 1.000 | 1.000 |
| task_success | llama | 0.300 | mac | 50 | 0.953 | 0.920 | 0.980 |
| task_success | llama | 0.300 | none | 50 | 1.000 | 1.000 | 1.000 |
| task_success | llama | 0.600 | ibac | 50 | 0.807 | 0.740 | 0.873 |
| task_success | llama | 0.600 | mac | 50 | 0.827 | 0.753 | 0.893 |
| task_success | llama | 0.600 | none | 50 | 0.980 | 0.953 | 1.000 |


## Utility floor

Difference in task success, IBAC minus the comparator, with a bootstrap interval; the floor is 5 points.


| model | p | comparator | n | n_excluded | diff | ci_low | ci_high | outcome |
|---|---|---|---|---|---|---|---|---|
| frontier_large | 0 | mac | 1 | 49 | 0.000 | 0.000 | 0.000 | met |
| frontier_large | 0 | none | 1 | 49 | 0.000 | 0.000 | 0.000 | met |
| frontier_large | 0.3 | mac | 1 | 49 | 0.000 | 0.000 | 0.000 | met |
| frontier_large | 0.3 | none | 1 | 49 | 0.000 | 0.000 | 0.000 | met |
| frontier_large | 0.6 | mac | 1 | 49 | -0.333 | -0.333 | -0.333 | not_met |
| frontier_large | 0.6 | none | 1 | 49 | -0.333 | -0.333 | -0.333 | not_met |
| frontier_large | all | mac | 1 | 49 | -0.111 | -0.111 | -0.111 | not_met |
| frontier_large | all | none | 1 | 49 | -0.111 | -0.111 | -0.111 | not_met |
| llama | 0 | mac | 50 | 0 | 0.000 | 0.000 | 0.000 | met |
| llama | 0 | none | 50 | 0 | 0.000 | 0.000 | 0.000 | met |
| llama | 0.3 | mac | 50 | 0 | 0.047 | 0.020 | 0.080 | met |
| llama | 0.3 | none | 50 | 0 | 0.000 | 0.000 | 0.000 | met |
| llama | 0.6 | mac | 50 | 0 | -0.020 | -0.113 | 0.080 | inconclusive |
| llama | 0.6 | none | 50 | 0 | -0.173 | -0.247 | -0.107 | not_met |
| llama | all | mac | 50 | 0 | 0.009 | -0.022 | 0.040 | met |
| llama | all | none | 50 | 0 | -0.058 | -0.082 | -0.036 | inconclusive |


Pooled over the failure rates:

- frontier_large, against mac: **not_met**. IBAC's task success is more than 5 points below mac's.

- frontier_large, against none: **not_met**. IBAC's task success is more than 5 points below none's.

- llama, against mac: **met**. IBAC's task success is not more than 5 points below mac's.

- llama, against none: **inconclusive**. The data neither show IBAC within 5 points of none nor more than 5 points below it.


## Mediator contrasts (Holm within each metric)

| metric | model | p | mediator_a | mediator_b | n | n_excluded | diff | p_wilcoxon | p_holm | reject_holm | cliffs_delta | magnitude | cohens_dz |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proposed_violation_rate | frontier_large | 0.000 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.000 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.000 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.300 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.300 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.300 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.600 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.600 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | frontier_large | 0.600 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| proposed_violation_rate | llama | 0.000 | ibac | mac | 50 | 0 | 0.004 | 0.901 | 1.000 | False | -0.014 | negligible | 0.023 |
| proposed_violation_rate | llama | 0.000 | ibac | none | 50 | 0 | -0.003 | 0.708 | 1.000 | False | -0.007 | negligible | -0.016 |
| proposed_violation_rate | llama | 0.000 | mac | none | 50 | 0 | -0.007 | 0.939 | 1.000 | False | -0.007 | negligible | -0.040 |
| proposed_violation_rate | llama | 0.300 | ibac | mac | 50 | 0 | 0.021 | 0.601 | 1.000 | False | 0.076 | negligible | 0.096 |
| proposed_violation_rate | llama | 0.300 | ibac | none | 50 | 0 | 0.045 | 0.168 | 1.000 | False | 0.133 | negligible | 0.232 |
| proposed_violation_rate | llama | 0.300 | mac | none | 50 | 0 | 0.024 | 0.380 | 1.000 | False | 0.078 | negligible | 0.129 |
| proposed_violation_rate | llama | 0.600 | ibac | mac | 50 | 0 | -0.003 | 0.977 | 1.000 | False | -0.041 | negligible | -0.021 |
| proposed_violation_rate | llama | 0.600 | ibac | none | 50 | 0 | 0.012 | 0.984 | 1.000 | False | 0.059 | negligible | 0.067 |
| proposed_violation_rate | llama | 0.600 | mac | none | 50 | 0 | 0.015 | 0.325 | 1.000 | False | 0.086 | negligible | 0.090 |
| executed_violation_rate | frontier_large | 0.000 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.000 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.000 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.300 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.300 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.300 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.600 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.600 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | frontier_large | 0.600 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| executed_violation_rate | llama | 0.000 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | llama | 0.000 | ibac | none | 50 | 0 | -0.308 | 0.000 | 0.000 | True | -0.860 | large | -1.332 |
| executed_violation_rate | llama | 0.000 | mac | none | 50 | 0 | -0.308 | 0.000 | 0.000 | True | -0.860 | large | -1.332 |
| executed_violation_rate | llama | 0.300 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | llama | 0.300 | ibac | none | 50 | 0 | -0.308 | 0.000 | 0.000 | True | -0.880 | large | -1.492 |
| executed_violation_rate | llama | 0.300 | mac | none | 50 | 0 | -0.308 | 0.000 | 0.000 | True | -0.880 | large | -1.492 |
| executed_violation_rate | llama | 0.600 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | llama | 0.600 | ibac | none | 50 | 0 | -0.379 | 0.000 | 0.000 | True | -0.940 | large | -2.126 |
| executed_violation_rate | llama | 0.600 | mac | none | 50 | 0 | -0.379 | 0.000 | 0.000 | True | -0.940 | large | -2.126 |
| blocked_rate | frontier_large | 0.000 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.000 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.000 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.300 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.300 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.300 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.600 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.600 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | frontier_large | 0.600 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| blocked_rate | llama | 0.000 | ibac | mac | 50 | 0 | 0.004 | 0.901 | 1.000 | False | -0.014 | negligible | 0.023 |
| blocked_rate | llama | 0.000 | ibac | none | 50 | 0 | 0.305 | 0.000 | 0.000 | True | 0.840 | large | 1.327 |
| blocked_rate | llama | 0.000 | mac | none | 50 | 0 | 0.301 | 0.000 | 0.000 | True | 0.880 | large | 1.472 |
| blocked_rate | llama | 0.300 | ibac | mac | 50 | 0 | 0.021 | 0.601 | 1.000 | False | 0.076 | negligible | 0.096 |
| blocked_rate | llama | 0.300 | ibac | none | 50 | 0 | 0.353 | 0.000 | 0.000 | True | 0.920 | large | 1.807 |
| blocked_rate | llama | 0.300 | mac | none | 50 | 0 | 0.332 | 0.000 | 0.000 | True | 0.960 | large | 1.825 |
| blocked_rate | llama | 0.600 | ibac | mac | 50 | 0 | -0.003 | 0.977 | 1.000 | False | -0.041 | negligible | -0.021 |
| blocked_rate | llama | 0.600 | ibac | none | 50 | 0 | 0.391 | 0.000 | 0.000 | True | 0.960 | large | 2.523 |
| blocked_rate | llama | 0.600 | mac | none | 50 | 0 | 0.394 | 0.000 | 0.000 | True | 0.960 | large | 2.306 |
| task_success | frontier_large | 0.000 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.000 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.000 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.300 | ibac | mac | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.300 | ibac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.300 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | frontier_large | 0.600 | ibac | mac | 1 | 49 | -0.333 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| task_success | frontier_large | 0.600 | ibac | none | 1 | 49 | -0.333 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| task_success | frontier_large | 0.600 | mac | none | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| task_success | llama | 0.000 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | llama | 0.000 | ibac | none | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | llama | 0.000 | mac | none | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | llama | 0.300 | ibac | mac | 50 | 0 | 0.047 | 0.008 | 0.130 | False | 0.140 | negligible | 0.399 |
| task_success | llama | 0.300 | ibac | none | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | llama | 0.300 | mac | none | 50 | 0 | -0.047 | 0.008 | 0.130 | False | -0.140 | negligible | -0.399 |
| task_success | llama | 0.600 | ibac | mac | 50 | 0 | -0.020 | 0.690 | 1.000 | False | -0.049 | negligible | -0.057 |
| task_success | llama | 0.600 | ibac | none | 50 | 0 | -0.173 | 0.000 | 0.002 | True | -0.388 | medium | -0.682 |
| task_success | llama | 0.600 | mac | none | 50 | 0 | -0.153 | 0.000 | 0.005 | True | -0.346 | medium | -0.584 |


## IBAC classifier

| model | p | runs | failed_runs | failure_rate |
|---|---|---|---|---|
| frontier_large | 0.000 | 3 | 0 | 0.000 |
| frontier_large | 0.300 | 3 | 0 | 0.000 |
| frontier_large | 0.600 | 3 | 0 | 0.000 |
| llama | 0.000 | 150 | 0 | 0.000 |
| llama | 0.300 | 150 | 0 | 0.000 |
| llama | 0.600 | 150 | 0 | 0.000 |


Accuracy against the benchmark's domain label: 42 of 50 scenarios (0.840), 0 unreadable.
