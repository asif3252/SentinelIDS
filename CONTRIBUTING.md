# Contributing

Contributions that improve correctness, reproducibility and analyst usability are welcome.

1. Open an issue describing the problem or proposal. Include a minimal synthetic example; never upload private traffic.
2. Create a branch and make a focused change.
3. Run `python -m unittest discover -s tests -v` and `python -m compileall -q app.py sentinel.py tests`.
4. For interface changes, manually verify both classifiers, all tabs, upload errors and CSV/JSON downloads.
5. Open a pull request explaining the problem, behavior after the change, validation performed and remaining limitations.

Dataset integrations must document provenance, redistribution rights, label mapping, exact units and split strategy. Keep derived features and preprocessing fitted only on training data. Do not claim real-world performance from synthetic examples or reuse a final test set for model selection.
