# RQ1: failure pressure and escalation

## Violation rate by cell

| mediator | model | p | n_scenarios | mean | ci_low | ci_high |
|---|---|---|---|---|---|---|
| ibac | frontier | 0.000 | 50 | 0.017 | 0.000 | 0.043 |
| ibac | frontier | 0.300 | 50 | 0.040 | 0.017 | 0.067 |
| ibac | frontier | 0.600 | 50 | 0.105 | 0.069 | 0.144 |
| ibac | llama | 0.000 | 50 | 0.305 | 0.242 | 0.368 |
| ibac | llama | 0.300 | 50 | 0.353 | 0.299 | 0.407 |
| ibac | llama | 0.600 | 50 | 0.391 | 0.348 | 0.433 |
| mac | frontier | 0.000 | 50 | 0.021 | 0.000 | 0.051 |
| mac | frontier | 0.300 | 50 | 0.016 | 0.000 | 0.038 |
| mac | frontier | 0.600 | 50 | 0.127 | 0.092 | 0.164 |
| mac | llama | 0.000 | 50 | 0.301 | 0.245 | 0.356 |
| mac | llama | 0.300 | 50 | 0.332 | 0.282 | 0.383 |
| mac | llama | 0.600 | 50 | 0.394 | 0.346 | 0.440 |
| none | frontier | 0.000 | 50 | 0.023 | 0.000 | 0.057 |
| none | frontier | 0.300 | 50 | 0.040 | 0.008 | 0.086 |
| none | frontier | 0.600 | 50 | 0.104 | 0.074 | 0.137 |
| none | llama | 0.000 | 50 | 0.308 | 0.244 | 0.371 |
| none | llama | 0.300 | 50 | 0.308 | 0.250 | 0.365 |
| none | llama | 0.600 | 50 | 0.379 | 0.331 | 0.427 |

## Primary contrast

Failure rate 0 to 0.6, mediator `none`, 50 scenarios (0 excluded for missing values).

- Llama delta: 0.071; frontier delta: 0.081
- Difference in differences (frontier minus Llama): **0.010**, 95% bootstrap interval [-0.046, 0.066]
- Paired Wilcoxon p = 0.9224; Cliff's delta = 0.027 (negligible); Cohen's dz = 0.047


The interval lies inside +/-0.12: the data rule out a difference as large as the 12%-point target, and any real difference is at most 0.066 (an upper bound, not an estimate).


## Contrasts (Holm within each kind)

| kind | mediator | model_a | p_a | model_b | p_b | n | n_excluded | diff | p_wilcoxon | p_holm | reject_holm | cliffs_delta | magnitude | cohens_dz |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| across_p | ibac | llama | 0.300 | llama | 0.000 | 50 | 0 | 0.048 | 0.087 | 0.437 | False | 0.160 | small | 0.245 |
| across_p | ibac | llama | 0.600 | llama | 0.000 | 50 | 0 | 0.086 | 0.013 | 0.118 | False | 0.264 | small | 0.367 |
| across_p | ibac | llama | 0.600 | llama | 0.300 | 50 | 0 | 0.038 | 0.180 | 0.719 | False | 0.101 | negligible | 0.202 |
| across_p | mac | llama | 0.300 | llama | 0.000 | 50 | 0 | 0.031 | 0.292 | 0.875 | False | 0.097 | negligible | 0.166 |
| across_p | mac | llama | 0.600 | llama | 0.000 | 50 | 0 | 0.093 | 0.004 | 0.041 | True | 0.292 | small | 0.393 |
| across_p | mac | llama | 0.600 | llama | 0.300 | 50 | 0 | 0.062 | 0.059 | 0.357 | False | 0.230 | small | 0.332 |
| across_p | none | llama | 0.300 | llama | 0.000 | 50 | 0 | 0.001 | 0.992 | 0.992 | False | 0.012 | negligible | 0.003 |
| across_p | none | llama | 0.600 | llama | 0.000 | 50 | 0 | 0.071 | 0.003 | 0.041 | True | 0.208 | small | 0.369 |
| across_p | none | llama | 0.600 | llama | 0.300 | 50 | 0 | 0.071 | 0.009 | 0.086 | False | 0.227 | small | 0.357 |
| across_p | ibac | frontier | 0.300 | frontier | 0.000 | 50 | 0 | 0.023 | 0.029 | 0.222 | False | 0.153 | small | 0.344 |
| across_p | ibac | frontier | 0.600 | frontier | 0.000 | 50 | 0 | 0.089 | 0.000 | 0.000 | True | 0.406 | medium | 0.743 |
| across_p | ibac | frontier | 0.600 | frontier | 0.300 | 50 | 0 | 0.066 | 0.001 | 0.018 | True | 0.275 | small | 0.530 |
| across_p | mac | frontier | 0.300 | frontier | 0.000 | 50 | 0 | -0.005 | 0.465 | 0.930 | False | -0.001 | negligible | -0.129 |
| across_p | mac | frontier | 0.600 | frontier | 0.000 | 50 | 0 | 0.106 | 0.000 | 0.001 | True | 0.556 | large | 0.739 |
| across_p | mac | frontier | 0.600 | frontier | 0.300 | 50 | 0 | 0.111 | 0.000 | 0.000 | True | 0.568 | large | 0.806 |
| across_p | none | frontier | 0.300 | frontier | 0.000 | 50 | 0 | 0.017 | 0.028 | 0.222 | False | 0.076 | negligible | 0.289 |
| across_p | none | frontier | 0.600 | frontier | 0.000 | 50 | 0 | 0.081 | 0.000 | 0.001 | True | 0.497 | large | 0.848 |
| across_p | none | frontier | 0.600 | frontier | 0.300 | 50 | 0 | 0.064 | 0.001 | 0.013 | True | 0.446 | medium | 0.532 |
| between_models | ibac | frontier | 0.000 | llama | 0.000 | 50 | 0 | -0.288 | 0.000 | 0.000 | True | -0.792 | large | -1.352 |
| between_models | mac | frontier | 0.000 | llama | 0.000 | 50 | 0 | -0.280 | 0.000 | 0.000 | True | -0.815 | large | -1.324 |
| between_models | none | frontier | 0.000 | llama | 0.000 | 50 | 0 | -0.284 | 0.000 | 0.000 | True | -0.792 | large | -1.144 |
| between_models | ibac | frontier | 0.300 | llama | 0.300 | 50 | 0 | -0.314 | 0.000 | 0.000 | True | -0.855 | large | -1.456 |
| between_models | mac | frontier | 0.300 | llama | 0.300 | 50 | 0 | -0.316 | 0.000 | 0.000 | True | -0.914 | large | -1.856 |
| between_models | none | frontier | 0.300 | llama | 0.300 | 50 | 0 | -0.268 | 0.000 | 0.000 | True | -0.776 | large | -1.121 |
| between_models | ibac | frontier | 0.600 | llama | 0.600 | 50 | 0 | -0.286 | 0.000 | 0.000 | True | -0.785 | large | -1.665 |
| between_models | mac | frontier | 0.600 | llama | 0.600 | 50 | 0 | -0.267 | 0.000 | 0.000 | True | -0.764 | large | -1.173 |
| between_models | none | frontier | 0.600 | llama | 0.600 | 50 | 0 | -0.275 | 0.000 | 0.000 | True | -0.788 | large | -1.284 |


## Page's trend across failure rates

| model | mediator | n | k | L | p_value |
|---|---|---|---|---|---|
| llama | ibac | 50 | 3 | 619.500 | 0.026 |
| llama | mac | 50 | 3 | 621.000 | 0.018 |
| llama | none | 50 | 3 | 625.000 | 0.006 |
| frontier | ibac | 50 | 3 | 634.500 | 0.000 |
| frontier | mac | 50 | 3 | 640.500 | 0.000 |
| frontier | none | 50 | 3 | 639.500 | 0.000 |
