# Development workflow

All changes after the initial scaffold go through a pull request. The initial scaffold commit predates this workflow.

1. Complete the relevant learning checkpoint before implementing a major research phase.
2. Start a focused branch from current `main`, such as `feat/market-data` or `fix/return-alignment`.
3. Implement the agreed scope and update relevant documentation and learning records.
4. Run checks appropriate to the change. For Python changes, run the test suite and configuration CLI documented in the README.
5. Commit and push the branch, then open a pull request using GitHub CLI.
6. Explain the problem, resulting behaviour, validation, and relevant research assumptions or limitations in the PR.
7. Review the changes with the project owner. Wait for their explicit approval to merge; do not enable automatic merging.
8. Merge after approval and successful required checks. Start the next change from updated `main`.

Keep PRs small enough to understand. Use one meaningful change or learning increment per PR rather than one PR per file edit. Do not push subsequent changes directly to `main`.

A public repository does not imply that credentials, local data, or unreviewed generated outputs belong in Git. Inspect the diff before publishing.

GitHub Actions provides automated checks. This documented process alone does not enforce branch protection in GitHub settings.
