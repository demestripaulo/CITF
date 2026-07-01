# Contributing to CITF

Contributions are welcome — issues, discussion, and pull requests.

## Ground rules

1. **Synthetic data only.** Never commit real, operational, employer, or client
   data to this repository, in any form. All datasets here are fictional and
   generated. Contributions that include real incident data will be declined.
2. **Single thesis.** CITF is focused on the convergence of physical and cyber
   security for under-resourced, security-dependent organizations. Please keep
   contributions aligned with that scope.
3. **Explainability.** Triage logic must remain transparent and auditable — a
   security manager has to be able to understand why an incident received its
   priority.

## Development

No external dependencies are required (Python 3.9+). Run the checks before
opening a pull request:

```bash
python tests/test_generator.py
python tests/test_sensors.py
```

## Style

- Standard library first; add a dependency only when it clearly earns its place.
- Keep the taxonomy, crosswalk, and severity rubric as the single source of
  truth in `citf/taxonomy.py` and `citf/triage.py`.
- Prefer small, well-named functions and clear docstrings.

## Reporting issues

Please include steps to reproduce, expected vs. actual behavior, and your
Python version. For anything security-sensitive, describe the concern without
including any real-world data.
