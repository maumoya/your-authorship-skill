# Changelog

## 0.1.0

- `authorship.py scan`: read-only sweep of local git repos, GitHub repos (license, owner) and the settings of Claude
  Code, Cursor CLI, Codex and Gemini CLI. One table with level, area, problem and fix id; `--json`, `--root`,
  `--no-github`, `--out`.
- `authorship.py fix ID`: shows the plan; `--apply` only after the user's yes, with a timestamped `.bak` copy.
- `commit-msg` hook: refuses a commit carrying an AI co-author trailer or "generated with" footer.
- `test-hook <repo>`: runs the installed hook on a trailer message and a normal one, so you can prove the block even where git cannot run; the installer also finds the hooks folder without git (worktrees, `--separate-git-dir`).
- GitHub Action (`action.yml`, Marketplace): fails a pull request or push whose new commits or tracked files give an AI
  tool author credit; `authorship.py check` runs the same check locally.
- History is reported as info only, never rewritten.
- Three eval cases (scan then ask, hook on yes, history stays) and a trigger test set.
