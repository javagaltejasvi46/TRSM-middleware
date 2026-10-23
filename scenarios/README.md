# TRSM Evaluation Scenarios

This directory contains versioned YAML scenario specifications used for reproducible testing and evaluation.

## Scenario Schema
Every scenario YAML defines:
- `id`: Unique identifier
- `name`: Human-readable title
- `category`: `benign` | `prompt_injection` | `memory_poisoning` | `role_hijacking` | `resource_authorization`
- `description`: Context and intended behavior
- `initial_task`: Prompt given to the workflow entry agent
- `expected_security_outcome`: `ALLOW` | `BLOCK` | `QUARANTINE` | `REVIEW`
- `ground_truth_label`: `benign` | `adversarial`
- `adversarial_objective_achieved_if`: Condition that marks attack success
