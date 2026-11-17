# Your Authorship Skill (directory edition)

You built it, so your name is the only one on it. This skill scans your local git repos and your AI tool
settings (Claude Code, Codex, Cursor, Gemini) for AI co-author trailers, "generated with" footers, AI credit lines
and AI commit identities. It shows one findings table, fixes each item only on your OK with a backup first, and
installs a commit-msg hook so new AI credit lines are blocked.

This folder is the **directory edition**: Markdown only. It ships no scripts. The skill does its work with Claude
Code's built-in tools (Read, Grep, Glob, Edit, Write, and Bash with `git`, `grep`, `find` and `sed`). The hook is
written into a repo only when you say yes to it, from the text in the skill file. Everything stays local: no
network calls, no telemetry.

## Full edition

The full edition lives at the repository root: <https://github.com/maumoya/your-authorship-skill>. It has the
scanner script, the GitHub Action, evals and benchmarks.

### Full edition only

- GitHub API checks through `gh`: contributors besides you, open PRs by bots or other accounts, and merged
  branches left on GitHub. Here you read the repo's Contributors page yourself.
- The `delete-branches:` fix (a GitHub repo setting).
- The CI check and GitHub Action that fail a pull request carrying AI credit.
- Multi-line author blocks: the full scanner also finds an AI named on the line under an "Authors:" heading.
  This edition matches single lines only.

## Install

From the plugin directory, install **your-authorship-skill**. The repository also has its own marketplace:

```
/plugin marketplace add maumoya/your-authorship-skill
/plugin install your-authorship-skill@your-authorship-skill
```

That marketplace entry installs the full edition from the repository root.

## Use

Say "authorship sweep" or `/your-authorship-skill`. See
[skills/your-authorship-skill/SKILL.md](skills/your-authorship-skill/SKILL.md).

## License

MIT. See [LICENSE](LICENSE).
