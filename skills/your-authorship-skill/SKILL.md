---
name: your-authorship-skill
description: Keeps you the sole author of your code when you build with AI agents. Scans every local repo, your GitHub account and your AI tool settings (Claude Code, Codex, Cursor, Gemini) for AI co-author trailers, "generated with" footers, AI credit lines in README, LICENSE or CODEOWNERS, and AI noreply commit identities; fixes each one only on your OK, with a backup; and installs a commit-msg hook so new ones are blocked. Use when the user says "/your-authorship-skill", "authorship sweep", "am I the author of my code", "remove AI co-author", "remove Co-Authored-By Claude", "stop Claude signing my commits", "turn off AI attribution", "who owns my code", "check my repos for AI credit", or asks to make sure every commit and file names only them.
license: MIT
---

# Your Authorship Skill

You built it, so your name is the only one on it. This skill finds every place an AI tool put its name on the
user's work, shows a short table, fixes each item only after the user says yes, and blocks new ones with a
commit-msg hook. Output: a findings table (high / medium / low / info), then a one-row-per-fix log with backups.

Paths below are relative to this skill's folder. The scanner is `scripts/authorship.py` (Python 3 standard library,
read-only unless `fix ID --apply`).

## Steps

1. **Who is the owner?** Use the name the user gave, else `git config --global user.name`. Ask once if neither exists.
   Pass it as `--owner "Full Name"` to every command.
2. **Scan (read-only):** `python3 scripts/authorship.py scan --owner "NAME"`. Add `--root DIR` (repeatable) when
   the user names folders; default is the home folder and common code folders. `--no-github` skips the GitHub check
   when `gh` is not signed in. `--json` for machine output.
3. **Show the table** exactly as the scan prints it: severity, where, what kind of hit, fix ID. Never paste the
   offending line itself back into chat or a file; describe it ("AI co-author trailer in 3 commits").
4. **Fix one at a time, on a yes.** For each fix ID, first run `python3 scripts/authorship.py fix ID` (shows the plan),
   ask the user, and only on a clear yes run `fix ID --apply`. Each apply keeps a `.bak-<timestamp>` backup and prints
   its path. Fix IDs: `claude-attribution`, `cursor-cli`, `claude-md`, `codex-agents`, `gemini-md`, `hook:<repo path>`,
   `delete-branches:<owner/repo>` (a GitHub repo setting, so no file backup; it is undone in the repo's Settings).
   After a hook install, prove it: `python3 scripts/authorship.py test-hook <repo>` runs the installed hook on a message
   with an AI co-author trailer (must be REFUSED) and a normal one (must be ALLOWED), the same way git calls it. It works
   even where `git` cannot run. Show its output; a real test commit is optional on top.
5. **Files the script does not edit** (README credit lines, LICENSE holder, CODEOWNERS): show the file and line number,
   propose the edit, and make it with the user's OK, one file at a time.
6. **History is info only.** Old commits with AI trailers are reported, never rewritten. Rewriting pushed history needs a
   force-push. Even when the user asks for it, do not do it: explain the cost (every commit hash changes, other clones
   and open PRs break, signatures are lost), recommend leaving history alone, and offer the hook (`fix hook:<repo>`) so
   new commits stay clean. The rewrite stays the user's own call, made by them.
7. **One author, checked three ways.** You (the repo owner's account) are the only author: no bot, no AI assistant.
   1. git: the history rows count AI and bot authors and AI trailers on every local branch and tag.
   2. GitHub API: per repo, the scan lists every contributor besides you (high), each open PR by a bot or another
      account (medium: merging it as that account adds a contributor; apply its change as your own commit and close
      it), and merged PR branches left on GitHub (low, `delete-branches:` fix: a kept branch keeps a bot commit alive).
   3. Rendered page: open each flagged repo's page and read "Contributors". It is cached apart from the API and can
      lag about 24 h after a fix; still wrong after 24 h with 1 and 2 clean means a GitHub Support ticket, not a pass.
8. **Re-scan** and show the before/after count: high and medium must be 0, or each one left has a reason.

## Done when

- The re-scan shows 0 high and 0 medium findings, or each remaining one is listed with the user's reason.
- Every fix was applied only after the user's yes for that fix ID, and its backup path was shown.
- No GitHub repo lists a contributor besides the owner, or each one left has the user's reason (the repo page
  read back, with the ~24 h lag noted).
- Each repo the user chose has the commit-msg hook, and `test-hook <repo>` printed `RESULT hook blocks AI credit`.

## Never

- Never write an AI co-author trailer, "generated with" footer or AI credit line, in any file, commit or reply.
- Never edit, commit, push or change settings without a yes for that exact item.
- Never rewrite or force-push git history.
- Never merge a bot's PR as the bot: that adds it as a contributor.
- Never send scan results anywhere; the only network calls are read-only `gh` reads (your login, your repo list
  with license info, and per repo its contributors, open PRs and branch setting), plus the one setting change a
  `delete-branches:` fix makes on a yes.
- Never claim done without the re-scan output.
