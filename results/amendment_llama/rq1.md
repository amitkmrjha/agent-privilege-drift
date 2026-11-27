# RQ1: failure pressure and escalation

## Violation rate by cell

| mediator | model | p | n_scenarios | mean | ci_low | ci_high |
|---|---|---|---|---|---|---|
| ibac | frontier_large | 0.000 | 1 | 0.000 | 0.000 | 0.000 |
| ibac | frontier_large | 0.300 | 1 | 0.000 | 0.000 | 0.000 |
| ibac | frontier_large | 0.600 | 1 | 0.000 | 0.000 | 0.000 |
| ibac | llama | 0.000 | 50 | 0.305 | 0.242 | 0.368 |
| ibac | llama | 0.300 | 50 | 0.353 | 0.299 | 0.407 |
| ibac | llama | 0.600 | 50 | 0.391 | 0.348 | 0.433 |
| mac | frontier_large | 0.000 | 1 | 0.000 | 0.000 | 0.000 |
| mac | frontier_large | 0.300 | 1 | 0.000 | 0.000 | 0.000 |
| mac | frontier_large | 0.600 | 1 | 0.000 | 0.000 | 0.000 |
| mac | llama | 0.000 | 50 | 0.301 | 0.245 | 0.356 |
| mac | llama | 0.300 | 50 | 0.332 | 0.282 | 0.383 |
| mac | llama | 0.600 | 50 | 0.394 | 0.346 | 0.440 |
| none | frontier_large | 0.000 | 50 | 0.000 | 0.000 | 0.000 |
| none | frontier_large | 0.300 | 50 | 0.000 | 0.000 | 0.000 |
| none | frontier_large | 0.600 | 50 | 0.004 | 0.000 | 0.011 |
| none | llama | 0.000 | 50 | 0.308 | 0.244 | 0.371 |
| none | llama | 0.300 | 50 | 0.308 | 0.250 | 0.365 |
| none | llama | 0.600 | 50 | 0.379 | 0.331 | 0.427 |

## Primary contrast

Failure rate 0 to 0.6, mediator `none`, 50 scenarios (0 excluded for missing values).

- Llama delta: 0.071; frontier_large delta: 0.004
- Difference in differences (frontier_large minus Llama): **-0.067**, 95% bootstrap interval [-0.123, -0.009]
- Paired Wilcoxon p = 0.0040; Cliff's delta = -0.338 (medium); Cohen's dz = -0.327


The interval reaches 0.123, so a difference as large as the 12%-point target is not ruled out.


## Contrasts (Holm within each kind)

| kind | mediator | model_a | p_a | model_b | p_b | n | n_excluded | diff | p_wilcoxon | p_holm | reject_holm | cliffs_delta | magnitude | cohens_dz |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| across_p | ibac | llama | 0.300 | llama | 0.000 | 50 | 0 | 0.048 | 0.087 | 1.000 | False | 0.160 | small | 0.245 |
| across_p | ibac | llama | 0.600 | llama | 0.000 | 50 | 0 | 0.086 | 0.013 | 0.196 | False | 0.264 | small | 0.367 |
| across_p | ibac | llama | 0.600 | llama | 0.300 | 50 | 0 | 0.038 | 0.180 | 1.000 | False | 0.101 | negligible | 0.202 |
| across_p | mac | llama | 0.300 | llama | 0.000 | 50 | 0 | 0.031 | 0.292 | 1.000 | False | 0.097 | negligible | 0.166 |
| across_p | mac | llama | 0.600 | llama | 0.000 | 50 | 0 | 0.093 | 0.004 | 0.064 | False | 0.292 | small | 0.393 |
| across_p | mac | llama | 0.600 | llama | 0.300 | 50 | 0 | 0.062 | 0.059 | 0.832 | False | 0.230 | small | 0.332 |
| across_p | none | llama | 0.300 | llama | 0.000 | 50 | 0 | 0.001 | 0.992 | 1.000 | False | 0.012 | negligible | 0.003 |
| across_p | none | llama | 0.600 | llama | 0.000 | 50 | 0 | 0.071 | 0.003 | 0.061 | False | 0.208 | small | 0.369 |
| across_p | none | llama | 0.600 | llama | 0.300 | 50 | 0 | 0.071 | 0.009 | 0.138 | False | 0.227 | small | 0.357 |
| across_p | ibac | frontier_large | 0.300 | frontier_large | 0.000 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | ibac | frontier_large | 0.600 | frontier_large | 0.000 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | ibac | frontier_large | 0.600 | frontier_large | 0.300 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | mac | frontier_large | 0.300 | frontier_large | 0.000 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | mac | frontier_large | 0.600 | frontier_large | 0.000 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | mac | frontier_large | 0.600 | frontier_large | 0.300 | 1 | 49 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | n/a |
| across_p | none | frontier_large | 0.300 | frontier_large | 0.000 | 50 | 0 | 0.000 | 1.000 | 1.000 | False | 0.000 | negligible | 0.000 |
| across_p | none | frontier_large | 0.600 | frontier_large | 0.000 | 50 | 0 | 0.004 | 0.180 | 1.000 | False | 0.040 | negligible | 0.197 |
| across_p | none | frontier_large | 0.600 | frontier_large | 0.300 | 50 | 0 | 0.004 | 0.180 | 1.000 | False | 0.040 | negligible | 0.197 |
| between_models | ibac | frontier_large | 0.000 | llama | 0.000 | 1 | 49 | -0.433 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| between_models | mac | frontier_large | 0.000 | llama | 0.000 | 1 | 49 | -0.361 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| between_models | none | frontier_large | 0.000 | llama | 0.000 | 50 | 0 | -0.308 | 0.000 | 0.000 | True | -0.860 | large | -1.332 |
| between_models | ibac | frontier_large | 0.300 | llama | 0.300 | 1 | 49 | -0.500 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| between_models | mac | frontier_large | 0.300 | llama | 0.300 | 1 | 49 | -0.650 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| between_models | none | frontier_large | 0.300 | llama | 0.300 | 50 | 0 | -0.308 | 0.000 | 0.000 | True | -0.880 | large | -1.492 |
| between_models | ibac | frontier_large | 0.600 | llama | 0.600 | 1 | 49 | -0.444 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| between_models | mac | frontier_large | 0.600 | llama | 0.600 | 1 | 49 | -0.498 | 1.000 | 1.000 | False | -1.000 | large | n/a |
| between_models | none | frontier_large | 0.600 | llama | 0.600 | 50 | 0 | -0.375 | 0.000 | 0.000 | True | -0.936 | large | -2.026 |


## Page's trend across failure rates

| model | mediator | n | k | L | p_value |
|---|---|---|---|---|---|
| llama | ibac | 50 | 3 | 619.500 | 0.026 |
| llama | mac | 50 | 3 | 621.000 | 0.018 |
| llama | none | 50 | 3 | 625.000 | 0.006 |
| frontier_large | none | 50 | 3 | 603.000 | 0.382 |
