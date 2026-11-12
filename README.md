<p align="center">
  <img src="assets/header.png" width="100%" alt="Your Authorship Skill: You built it. Your name on it. Scans your repos, GitHub and AI tool settings, turns AI attribution off and installs a hook that blocks new AI credit.">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Claude%20Code-skill%20%2B%20plugin-7c5cfc" alt="Claude Code skill and plugin">
  <a href="#results-measured-2026-11-05"><img src="https://img.shields.io/badge/runs%20passed-%2B100%20pts-2da44e" alt="runs passed: +100 pts"></a>
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license">
  <a href="https://opensource.org/license/mit"><img src="https://img.shields.io/badge/Open%20Source-OSI%20approved%20license-3DA639?logo=opensourceinitiative&logoColor=white" alt="Open Source: OSI-approved MIT license"></a>
  <img src="https://img.shields.io/badge/privacy-no%20tracking%20%C2%B7%20no%20data%20collected-7c5cfc" alt="Privacy: no tracking, no data collected">
  <a href="https://scorecard.dev/viewer/?uri=github.com/maumoya/your-authorship-skill"><img src="https://api.scorecard.dev/projects/github.com/maumoya/your-authorship-skill/badge" alt="OpenSSF Scorecard"></a>
  <a href="https://www.bestpractices.dev/projects/16372"><img src="https://www.bestpractices.dev/projects/16372/badge" alt="OpenSSF Best Practices: passing"></a>
</p>

<p align="center">
  <img src="assets/demo.gif" width="720" alt="Demo: a scan finds a repo with no commit-msg hook, the hook is installed on a yes, a commit carrying an AI co-author trailer is refused, a normal commit goes through, and the re-scan shows 0 high, 0 medium.">
</p>

<p align="center">
  <a href="#results-measured-2026-11-05"><img src="assets/bench-card.svg" alt="100% of eval runs passed with the skill, 0% without it; grader score 100% vs 31%; 3% less spend and 16% more time per run (measured 2026-11-05)" width="760"></a>
</p>

# Your Authorship Skill

**You built it. Your name on it.** AI coding agents add their own name to your work: a co-author trailer on
commits, a "generated with" footer on pull requests, credit lines in docs. This skill finds every one across your
local repos, your GitHub account and your AI tool settings, turns each source off only on your OK, and installs a
`commit-msg` hook so new ones are refused.

## Install

Claude Code plugin:

```
/plugin marketplace add maumoya/your-authorship-skill
/plugin install your-authorship-skill@your-authorship-skill
```

Any agent that reads skills:

```
npx skills add maumoya/your-authorship-skill
```

Pin a release: `npx skills add maumoya/your-authorship-skill@v0.2.0`.

## Use

Type `/your-authorship-skill`, or just ask: "am I the author of my code?", "remove the AI co-author from my commits",
"stop Claude signing my commits", "check my repos for AI credit".

The skill then:

1. **Scans**, read-only: the git repos in your home, Projects, Developer and code folders (or the `--root` you give),
   your GitHub repos (license and owner), and the settings of Claude Code, Cursor CLI, Codex and Gemini CLI. You get
   one table: level, area, what is wrong, the fix id.
2. **Asks** before every change. `fix ID` shows the plan; only on your yes does it run `fix ID --apply`, and each
   edited file keeps a timestamped `.bak` copy.
3. **Installs the hook** in the repos you pick. A commit that carries an AI co-author trailer or "generated with"
   footer is refused; a normal commit goes through. `test-hook` proves both on the spot.
4. **Leaves history alone.** Old commits with AI credit are listed as info. It never rewrites or force-pushes.
5. **One author, checked three ways.** git history (AI and bot authors on every branch and tag), the GitHub API
   (any contributor besides you, open bot PRs that must never be merged as the bot, merged branches left on
   GitHub), and the repo page's Contributors read back (it can lag about 24 h).
6. **Re-scans** and shows the before and after counts.

Run the scanner on its own:

```
python3 skills/your-authorship-skill/scripts/authorship.py scan --owner "Your Name"
python3 skills/your-authorship-skill/scripts/authorship.py scan --owner "Your Name" --root ~/code --no-github --json
python3 skills/your-authorship-skill/scripts/authorship.py test-hook ~/code/my-app   # proves the hook refuses AI credit
```

| Fix id | What it changes |
|---|---|
| `claude-attribution` | Claude Code settings: commit and PR attribution off |
| `cursor-cli` | Cursor CLI config: agent commit attribution off |
| `claude-md`, `codex-agents`, `gemini-md` | That tool's global rules file gets an authorship rule |
| `hook:<repo path>` | Installs the `commit-msg` hook in that repo |
| `delete-branches:<owner/repo>` | GitHub deletes a PR's branch after merge, so no old bot commit stays reachable |

README, LICENSE and CODEOWNERS edits are suggested, never made without your OK.

## Use in CI (GitHub Action)

Fail any pull request whose new commits or files give an AI tool author credit:

```yaml
name: Authorship
on: [pull_request, push]
permissions: read-all
jobs:
  authorship:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - uses: maumoya/your-authorship-skill@v0.2.0
```

It checks only the commits the pull request (or push) adds, so old history never blocks you, plus the tracked files.
Inputs: `range` (any git range), `files: "false"` to skip files, `path`. Output: `findings`. Locally:
`authorship.py check . --range origin/main..HEAD`.

## Results (measured 2026-11-05)

Method: `bench.sh` ran `claude plugin eval` on 3 cases, 3 runs each, with the skill and without it
(claude 2.1.316). Score is the share of graders passed per run; a run passes when every grader passes.

| | With the skill | Without | Change |
|---|---:|---:|---:|
| Runs passed | 100% | 0% | +100 pts |
| Score (mean ± sd) | 1 ± 0 | 0.31 ± 0.18 | +0.69 |
| Spend per run (USD) | 0.161 | 0.167 | -3% |
| Time per run (s) | 42 | 36 | +16% |
| Turns per run | 4.2 | 4.7 | |

| Case | Passed with | Passed without |
|---|---:|---:|
| history-stays | 3/3 | 0/3 |
| hook-on-yes | 3/3 | 0/3 |
| scan-then-ask | 3/3 | 0/3 |

Trigger test: the skill was picked for 88% of the phrases that should start it and for 0% of the near misses that should not (36 runs, `evals/triggers.json`).

Real sweep: one scan read 46 local repos and the four AI tool settings in 29 s, read-only.

Re-run it: `bench.sh . --yes` from [skill-forger-e2e](https://github.com/maumoya/skill-forger-e2e) (billed to your account).

## FAQ

### Why does this matter?

Your commits, releases and license name who made the work. Hiring managers, clients and lawyers read those. An AI
agent is a tool, like your editor: it should not sign your work.

### Does it send my data anywhere?

No. It runs locally. The only network calls are read-only `gh` reads: your login, your repo list with license
info, and per repo its contributors, open PRs and branch setting. The one write is the `delete-branches:` fix, on your yes. Skip both with `--no-github`.

### Will it rewrite my git history?

No. Past commits that carry AI credit are listed as info only. Rewriting pushed history breaks other people's clones,
so that call stays yours.

### Which tools does it cover?

Claude Code, Cursor CLI, Codex and Gemini CLI settings and rules files, your local git repos and your GitHub repos.
The hook works with any tool that commits through git.

### Can I remove the hook?

Yes. Delete `.git/hooks/commit-msg` in that repo, or restore the `.bak` copy the skill made.

## About the author

Hi, I'm **Mauricio Alonso Moya Tapia** ([@maumoya](https://github.com/maumoya)). I built your-authorship-skill
because I build with AI agents every day and kept finding their names on my work after I had turned them off.
I wanted one sweep that checks everything and one hook that keeps it that way.

More of my work: [skill-forger-e2e](https://github.com/maumoya/skill-forger-e2e), which shipped this skill end to
end, and [adhd-status](https://github.com/maumoya/adhd-status), an ADHD-friendly status board skill for Claude Code.

Say hi or follow my work on [LinkedIn](https://www.linkedin.com/in/mba-mmoyat/).

## License

MIT © 2026 Mauricio Alonso Moya Tapia
