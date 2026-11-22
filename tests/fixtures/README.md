# Test fixtures

`toolprivbench_sample.jsonl`: three unmodified records copied from ToolPrivBench
(BAAI/ToolPrivBench, revision a86a3e8, CC-BY-4.0; Yang et al., arXiv 2606.20023). Two have no
`parameters` field and one (`BIZ-SCOPE-001`) has typed parameters and empty `simulation_error`
on its risk tools. They let the loader tests run in CI without downloading the full data.
