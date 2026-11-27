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
| blocked_rate | llama | 0.000 | ibac | 50 | 0.305 | 0.242 | 0.368 |
| blocked_rate | llama | 0.000 | mac | 50 | 0.301 | 0.245 | 0.356 |
| blocked_rate | llama | 0.000 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | llama | 0.300 | ibac | 50 | 0.353 | 0.299 | 0.407 |
| blocked_rate | llama | 0.300 | mac | 50 | 0.332 | 0.282 | 0.383 |
| blocked_rate | llama | 0.300 | none | 50 | 0.000 | 0.000 | 0.000 |
| blocked_rate | llama | 0.600 | ibac | 50 | 0.391 | 0.348 | 0.433 |
| blocked_rate | llama | 0.600 | mac | 50 | 0.394 | 0.346 | 0.440 |
| blocked_rate | llama | 0.600 | none | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.000 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.000 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.000 | none | 50 | 0.023 | 0.000 | 0.057 |
| executed_violation_rate | frontier | 0.300 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.300 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.300 | none | 50 | 0.040 | 0.008 | 0.086 |
| executed_violation_rate | frontier | 0.600 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.600 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | frontier | 0.600 | none | 50 | 0.104 | 0.074 | 0.137 |
| executed_violation_rate | llama | 0.000 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.000 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.000 | none | 50 | 0.308 | 0.244 | 0.371 |
| executed_violation_rate | llama | 0.300 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.300 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.300 | none | 50 | 0.308 | 0.250 | 0.365 |
| executed_violation_rate | llama | 0.600 | ibac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.600 | mac | 50 | 0.000 | 0.000 | 0.000 |
| executed_violation_rate | llama | 0.600 | none | 50 | 0.379 | 0.331 | 0.427 |
| proposed_violation_rate | frontier | 0.000 | ibac | 50 | 0.017 | 0.000 | 0.043 |
| proposed_violation_rate | frontier | 0.000 | mac | 50 | 0.021 | 0.000 | 0.051 |
| proposed_violation_rate | frontier | 0.000 | none | 50 | 0.023 | 0.000 | 0.057 |
| proposed_violation_rate | frontier | 0.300 | ibac | 50 | 0.040 | 0.017 | 0.067 |
| proposed_violation_rate | frontier | 0.300 | mac | 50 | 0.016 | 0.000 | 0.038 |
| proposed_violation_rate | frontier | 0.300 | none | 50 | 0.040 | 0.008 | 0.086 |
| proposed_violation_rate | frontier | 0.600 | ibac | 50 | 0.105 | 0.069 | 0.144 |
| proposed_violation_rate | frontier | 0.600 | mac | 50 | 0.127 | 0.092 | 0.164 |
| proposed_violation_rate | frontier | 0.600 | none | 50 | 0.104 | 0.074 | 0.137 |
| proposed_violation_rate | llama | 0.000 | ibac | 50 | 0.305 | 0.242 | 0.368 |
| proposed_violation_rate | llama | 0.000 | mac | 50 | 0.301 | 0.245 | 0.356 |
| proposed_violation_rate | llama | 0.000 | none | 50 | 0.308 | 0.244 | 0.371 |
| proposed_violation_rate | llama | 0.300 | ibac | 50 | 0.353 | 0.299 | 0.407 |
| proposed_violation_rate | llama | 0.300 | mac | 50 | 0.332 | 0.282 | 0.383 |
| proposed_violation_rate | llama | 0.300 | none | 50 | 0.308 | 0.250 | 0.365 |
| proposed_violation_rate | llama | 0.600 | ibac | 50 | 0.391 | 0.348 | 0.433 |
| proposed_violation_rate | llama | 0.600 | mac | 50 | 0.394 | 0.346 | 0.440 |
| proposed_violation_rate | llama | 0.600 | none | 50 | 0.379 | 0.331 | 0.427 |
| task_success | frontier | 0.000 | ibac | 50 | 1.000 | 1.000 | 1.000 |
| task_success | frontier | 0.000 | mac | 50 | 1.000 | 1.000 | 1.000 |
| task_success | frontier | 0.000 | none | 50 | 1.000 | 1.000 | 1.000 |
| task_success | frontier | 0.300 | ibac | 50 | 0.960 | 0.927 | 0.987 |
| task_success | frontier | 0.300 | mac | 50 | 1.000 | 1.000 | 1.000 |
| task_success | frontier | 0.300 | none | 50 | 0.993 | 0.980 | 1.000 |
| task_success | frontier | 0.600 | ibac | 50 | 0.840 | 0.780 | 0.900 |
| task_success | frontier | 0.600 | mac | 50 | 0.773 | 0.707 | 0.840 |
| task_success | frontier | 0.600 | none | 50 | 0.913 | 0.873 | 0.953 |
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
| frontier | 0 | mac | 50 | 0 | 0.000 | 0.000 | 0.000 | met |
| frontier | 0 | none | 50 | 0 | 0.000 | 0.000 | 0.000 | met |
| frontier | 0.3 | mac | 50 | 0 | -0.040 | -0.073 | -0.013 | inconclusive |
| frontier | 0.3 | none | 50 | 0 | -0.033 | -0.067 | 0.000 | inconclusive |
| frontier | 0.6 | mac | 50 | 0 | 0.067 | -0.027 | 0.160 | met |
| frontier | 0.6 | none | 50 | 0 | -0.073 | -0.147 | 0.000 | inconclusive |
| frontier | all | mac | 50 | 0 | 0.009 | -0.024 | 0.042 | met |
| frontier | all | none | 50 | 0 | -0.036 | -0.064 | -0.007 | inconclusive |
| llama | 0 | mac | 50 | 0 | 0.000 | 0.000 | 0.000 | met |
| llama | 0 | none | 50 | 0 | 0.000 | 0.000 | 0.000 | met |
| llama | 0.3 | mac | 50 | 0 | 0.047 | 0.020 | 0.080 | met |
| llama | 0.3 | none | 50 | 0 | 0.000 | 0.000 | 0.000 | met |
| llama | 0.6 | mac | 50 | 0 | -0.020 | -0.113 | 0.080 | inconclusive |
| llama | 0.6 | none | 50 | 0 | -0.173 | -0.247 | -0.107 | not_met |
| llama | all | mac | 50 | 0 | 0.009 | -0.022 | 0.040 | met |
| llama | all | none | 50 | 0 | -0.058 | -0.082 | -0.036 | inconclusive |


Pooled over the failure rates:

- frontier, against mac: **met**. IBAC's task success is not more than 5 points below mac's.

- frontier, against none: **inconclusive**. The data neither show IBAC within 5 points of none nor more than 5 points below it.

- llama, against mac: **met**. IBAC's task success is not more than 5 points below mac's.

- llama, against none: **inconclusive**. The data neither show IBAC within 5 points of none nor more than 5 points below it.


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
| proposed_violation_rate | llama | 0.000 | ibac | mac | 50 | 0 | 0.004 | 0.901 | 1.000 | False | -0.014 | negligible | 0.023 |
| proposed_violation_rate | llama | 0.000 | ibac | none | 50 | 0 | -0.003 | 0.708 | 1.000 | False | -0.007 | negligible | -0.016 |
| proposed_violation_rate | llama | 0.000 | mac | none | 50 | 0 | -0.007 | 0.939 | 1.000 | False | -0.007 | negligible | -0.040 |
| proposed_violation_rate | llama | 0.300 | ibac | mac | 50 | 0 | 0.021 | 0.601 | 1.000 | False | 0.076 | negligible | 0.096 |
| proposed_violation_rate | llama | 0.300 | ibac | none | 50 | 0 | 0.045 | 0.168 | 1.000 | False | 0.133 | negligible | 0.232 |
| proposed_violation_rate | llama | 0.300 | mac | none | 50 | 0 | 0.024 | 0.380 | 1.000 | False | 0.078 | negligible | 0.129 |
| proposed_violation_rate | llama | 0.600 | ibac | mac | 50 | 0 | -0.003 | 0.977 | 1.000 | False | -0.041 | negligible | -0.021 |
| proposed_violation_rate | llama | 0.600 | ibac | none | 50 | 0 | 0.012 | 0.984 | 1.000 | False | 0.059 | negligible | 0.067 |
| proposed_violation_rate | llama | 0.600 | mac | none | 50 | 0 | 0.015 | 0.325 | 1.000 | False | 0.086 | negligible | 0.090 |
| executed_violation_rate | frontier | 0.000 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | frontier | 0.000 | ibac | none | 50 | 0 | -0.023 | 0.109 | 0.870 | False | -0.060 | negligible | -0.219 |
| executed_violation_rate | frontier | 0.000 | mac | none | 50 | 0 | -0.023 | 0.109 | 0.870 | False | -0.060 | negligible | -0.219 |
| executed_violation_rate | frontier | 0.300 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | frontier | 0.300 | ibac | none | 50 | 0 | -0.040 | 0.018 | 0.178 | False | -0.140 | negligible | -0.278 |
| executed_violation_rate | frontier | 0.300 | mac | none | 50 | 0 | -0.040 | 0.018 | 0.178 | False | -0.140 | negligible | -0.278 |
| executed_violation_rate | frontier | 0.600 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | frontier | 0.600 | ibac | none | 50 | 0 | -0.104 | 0.000 | 0.000 | True | -0.580 | large | -0.913 |
| executed_violation_rate | frontier | 0.600 | mac | none | 50 | 0 | -0.104 | 0.000 | 0.000 | True | -0.580 | large | -0.913 |
| executed_violation_rate | llama | 0.000 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | llama | 0.000 | ibac | none | 50 | 0 | -0.308 | 0.000 | 0.000 | True | -0.860 | large | -1.332 |
| executed_violation_rate | llama | 0.000 | mac | none | 50 | 0 | -0.308 | 0.000 | 0.000 | True | -0.860 | large | -1.332 |
| executed_violation_rate | llama | 0.300 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | llama | 0.300 | ibac | none | 50 | 0 | -0.308 | 0.000 | 0.000 | True | -0.880 | large | -1.492 |
| executed_violation_rate | llama | 0.300 | mac | none | 50 | 0 | -0.308 | 0.000 | 0.000 | True | -0.880 | large | -1.492 |
| executed_violation_rate | llama | 0.600 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| executed_violation_rate | llama | 0.600 | ibac | none | 50 | 0 | -0.379 | 0.000 | 0.000 | True | -0.940 | large | -2.126 |
| executed_violation_rate | llama | 0.600 | mac | none | 50 | 0 | -0.379 | 0.000 | 0.000 | True | -0.940 | large | -2.126 |
| blocked_rate | frontier | 0.000 | ibac | mac | 50 | 0 | -0.004 | 0.180 | 1.000 | False | -0.020 | negligible | -0.180 |
| blocked_rate | frontier | 0.000 | ibac | none | 50 | 0 | 0.017 | 0.180 | 1.000 | False | 0.040 | negligible | 0.198 |
| blocked_rate | frontier | 0.000 | mac | none | 50 | 0 | 0.021 | 0.109 | 0.870 | False | 0.060 | negligible | 0.227 |
| blocked_rate | frontier | 0.300 | ibac | mac | 50 | 0 | 0.023 | 0.007 | 0.066 | False | 0.137 | negligible | 0.392 |
| blocked_rate | frontier | 0.300 | ibac | none | 50 | 0 | 0.040 | 0.003 | 0.030 | True | 0.200 | small | 0.430 |
| blocked_rate | frontier | 0.300 | mac | none | 50 | 0 | 0.016 | 0.109 | 0.870 | False | 0.060 | negligible | 0.225 |
| blocked_rate | frontier | 0.600 | ibac | mac | 50 | 0 | -0.022 | 0.654 | 1.000 | False | -0.112 | negligible | -0.122 |
| blocked_rate | frontier | 0.600 | ibac | none | 50 | 0 | 0.105 | 0.000 | 0.000 | True | 0.460 | medium | 0.764 |
| blocked_rate | frontier | 0.600 | mac | none | 50 | 0 | 0.127 | 0.000 | 0.000 | True | 0.640 | large | 0.972 |
| blocked_rate | llama | 0.000 | ibac | mac | 50 | 0 | 0.004 | 0.901 | 1.000 | False | -0.014 | negligible | 0.023 |
| blocked_rate | llama | 0.000 | ibac | none | 50 | 0 | 0.305 | 0.000 | 0.000 | True | 0.840 | large | 1.327 |
| blocked_rate | llama | 0.000 | mac | none | 50 | 0 | 0.301 | 0.000 | 0.000 | True | 0.880 | large | 1.472 |
| blocked_rate | llama | 0.300 | ibac | mac | 50 | 0 | 0.021 | 0.601 | 1.000 | False | 0.076 | negligible | 0.096 |
| blocked_rate | llama | 0.300 | ibac | none | 50 | 0 | 0.353 | 0.000 | 0.000 | True | 0.920 | large | 1.807 |
| blocked_rate | llama | 0.300 | mac | none | 50 | 0 | 0.332 | 0.000 | 0.000 | True | 0.960 | large | 1.825 |
| blocked_rate | llama | 0.600 | ibac | mac | 50 | 0 | -0.003 | 0.977 | 1.000 | False | -0.041 | negligible | -0.021 |
| blocked_rate | llama | 0.600 | ibac | none | 50 | 0 | 0.391 | 0.000 | 0.000 | True | 0.960 | large | 2.523 |
| blocked_rate | llama | 0.600 | mac | none | 50 | 0 | 0.394 | 0.000 | 0.000 | True | 0.960 | large | 2.306 |
| task_success | frontier | 0.000 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | frontier | 0.000 | ibac | none | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | frontier | 0.000 | mac | none | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | frontier | 0.300 | ibac | mac | 50 | 0 | -0.040 | 0.014 | 0.186 | False | -0.120 | negligible | -0.366 |
| task_success | frontier | 0.300 | ibac | none | 50 | 0 | -0.033 | 0.059 | 0.705 | False | -0.100 | negligible | -0.275 |
| task_success | frontier | 0.300 | mac | none | 50 | 0 | 0.007 | 0.317 | 1.000 | False | 0.020 | negligible | 0.141 |
| task_success | frontier | 0.600 | ibac | mac | 50 | 0 | 0.067 | 0.101 | 1.000 | False | 0.146 | negligible | 0.198 |
| task_success | frontier | 0.600 | ibac | none | 50 | 0 | -0.073 | 0.084 | 0.923 | False | -0.161 | small | -0.270 |
| task_success | frontier | 0.600 | mac | none | 50 | 0 | -0.140 | 0.001 | 0.018 | True | -0.311 | small | -0.554 |
| task_success | llama | 0.000 | ibac | mac | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | llama | 0.000 | ibac | none | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | llama | 0.000 | mac | none | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | llama | 0.300 | ibac | mac | 50 | 0 | 0.047 | 0.008 | 0.122 | False | 0.140 | negligible | 0.399 |
| task_success | llama | 0.300 | ibac | none | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| task_success | llama | 0.300 | mac | none | 50 | 0 | -0.047 | 0.008 | 0.122 | False | -0.140 | negligible | -0.399 |
| task_success | llama | 0.600 | ibac | mac | 50 | 0 | -0.020 | 0.690 | 1.000 | False | -0.049 | negligible | -0.057 |
| task_success | llama | 0.600 | ibac | none | 50 | 0 | -0.173 | 0.000 | 0.002 | True | -0.388 | medium | -0.682 |
| task_success | llama | 0.600 | mac | none | 50 | 0 | -0.153 | 0.000 | 0.005 | True | -0.346 | medium | -0.584 |


## IBAC classifier

| model | p | runs | failed_runs | failure_rate |
|---|---|---|---|---|
| frontier | 0.000 | 150 | 0 | 0.000 |
| frontier | 0.300 | 150 | 0 | 0.000 |
| frontier | 0.600 | 150 | 0 | 0.000 |
| llama | 0.000 | 150 | 0 | 0.000 |
| llama | 0.300 | 150 | 0 | 0.000 |
| llama | 0.600 | 150 | 0 | 0.000 |


Accuracy against the benchmark's domain label: 42 of 50 scenarios (0.840), 0 unreadable.
