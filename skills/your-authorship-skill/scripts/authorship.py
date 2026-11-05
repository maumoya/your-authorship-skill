#!/usr/bin/env python3
"""Authorship sweep: find AI credit lines in your repos and AI tool settings; fix one at a time on your OK.

Read-only by default. `scan` reports; `fix ID` shows one change; `fix ID --apply` makes it (backup kept).
Pushed history is never rewritten: old commits are reported as info only.

    python3 authorship.py scan [--json] [--no-github] [--out FILE] [--root DIR ...] [--owner NAME]
    python3 authorship.py fix ID [--apply]
    python3 authorship.py message FILE       # check one commit message (what the hook runs)
    python3 authorship.py text < body.md     # check a PR body or any text

Pure standard library, Python 3.8+. The patterns are built from pieces so this file never matches itself.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK_SRC = HERE / "commit-msg"
HOOK_MARKER = "# your-authorship-skill: commit-msg"
MAX_FILE = 2_000_000

# ---------- patterns ----------

_AI = (r"(claude|anthropic|codex|openai|chatgpt|gpt-?\d|copilot|gemini|bard|cursor|devin-ai|windsurf|codeium"
       r"|tabnine|aider|grok|mistral|deepseek|qwen|minimax|llama|coderabbit|sweep-ai)")
_NOREPLY = "noreply" + "@" + r"(anthropic|openai)" + r"\.com"
CO_AUTHOR = re.compile(r"^\W*co-" + r"authored-by:.*\b" + _AI, re.I)
FOOTER = re.compile(r"generated " + r"(with|by) \[?" + _AI, re.I)
NOREPLY = re.compile(_NOREPLY, re.I)
_LABEL = (r"(authors?|co-?authors?|credits?|maintainers?|creators?"
          r"|(written|created|authored|developed|built|made|coded|designed)\s+(by|with))")
_NAMED = r"(name\W*)?(an?\s+|the\s+)?" + _AI + r"\b"
CREDIT = re.compile(r"^\W*" + _LABEL + r"\b[^\w\n]*" + _NAMED, re.I)
CREDIT_BLOCK = re.compile(r"^\W*" + _LABEL + r"[^\w\n]*$", re.I)
CREDIT_ITEM = re.compile(r"^\W*" + _NAMED, re.I)
_CONTINUATION = re.compile(r"^\s*([-*]\s|name\s*[:=])", re.I)
SESSION = re.compile(r"^\W*claude-" + r"session:", re.I)
AI_IDENTITY = re.compile(r"^(github-)?" + _AI + r"\b|^(\d+\+)?(github-)?" + _AI + r"[\w.\[\]-]*@|" + _NOREPLY,
                         re.I)


def _hit(line: str) -> str:
    """The kind of AI credit on a line, or ''. Reports describe the kind, never repeat the line."""
    if CO_AUTHOR.search(line):
        return "AI co-author trailer"
    if FOOTER.search(line):
        return "AI generated-with footer"
    if NOREPLY.search(line):
        return "AI vendor noreply address"
    if CREDIT.search(line):
        return "AI credit line"
    if SESSION.search(line):
        return "AI session link trailer"
    return ""


def findings(text: str) -> list:
    """(line number, kind) for every AI credit in TEXT, including multi-line author blocks."""
    lines, out = text.splitlines(), []
    for i, line in enumerate(lines):
        kind = _hit(line)
        if kind:
            out.append((i + 1, kind))
        elif CREDIT_BLOCK.match(line):
            indent = len(line) - len(line.lstrip())
            for j, item in enumerate(lines[i + 1:i + 13], i + 2):
                if not item.strip() or not (len(item) - len(item.lstrip()) > indent or _CONTINUATION.match(item)):
                    break
                if CREDIT_ITEM.match(item) and not _hit(item):
                    out.append((j, "AI named in an author block"))
    return out


def identity(name: str, email: str) -> bool:
    return bool(AI_IDENTITY.search(name.strip()) or AI_IDENTITY.search(email.strip()))


# ---------- helpers ----------

def home() -> Path:
    return Path(os.environ.get("AUTHORSHIP_HOME") or Path.home())


def _run(cmd, cwd=None):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as e:
        return subprocess.CompletedProcess(cmd, 127, "", str(e))


def _git(repo: Path, *args) -> str:
    r = _run(["git", "-C", str(repo), *args])
    return r.stdout if r.returncode == 0 else ""


def owner_name(given: str = "") -> str:
    return (given or os.environ.get("AUTHORSHIP_OWNER") or _git(home(), "config", "--global", "user.name").strip()
            or "the repository owner")


def _finding(area, target, problem, fix_id="", fix="", level="medium"):
    return {"level": level, "area": area, "target": target, "problem": problem, "fix_id": fix_id, "fix": fix}


def _decode(data: bytes) -> str:
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", errors="replace")
    text = data.decode("utf-8", errors="replace")
    if b"\x00" in data:
        text += "\n" + data.replace(b"\x00", b"").decode("utf-8", errors="replace")
    return text


def _json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _summary(hits) -> str:
    kinds = sorted({k for _, k in hits})
    lines = ", ".join(str(n) for n, _ in hits[:5]) + (" …" if len(hits) > 5 else "")
    return f"{'; '.join(kinds)} at line {lines}"


# ---------- repos ----------

def local_repos(roots=None) -> list:
    h = home()
    roots = [Path(r).expanduser() for r in roots] if roots else [h, h / "Projects", h / "Developer", h / "code",
                                                                   h / "src", h / "tools"]
    seen, out = set(), []
    for root in roots:
        if not root.is_dir():
            continue
        cands = [root] + [p for p in sorted(root.iterdir()) if p.is_dir() and not p.name.startswith(".")]
        for p in cands:
            if (p / ".git").exists():
                key = p.resolve()
                if key not in seen:
                    seen.add(key)
                    out.append(p)
    return out


def hooks_dir(repo: Path):
    custom = _git(repo, "config", "--get", "core.hooksPath").strip()
    if custom:
        return None, custom
    common = _git(repo, "rev-parse", "--git-common-dir").strip()
    if not common:
        return None, ""
    p = Path(common)
    return (p if p.is_absolute() else repo / p) / "hooks", ""


def check_hook(repo: Path) -> list:
    d, custom = hooks_dir(repo)
    if custom:
        hook = (repo / custom / "commit-msg") if not Path(custom).is_absolute() else Path(custom) / "commit-msg"
        if hook.is_file() and HOOK_MARKER in hook.read_text(errors="replace"):
            return []
        return [_finding("repo", repo.name, f"core.hooksPath is set ({custom}), so the hook cannot be added "
                         "automatically", fix=f"copy {HOOK_SRC.name} into that folder by hand", level="high")]
    if d is None:
        return []
    hook = d / "commit-msg"
    if hook.is_file() and HOOK_MARKER in hook.read_text(errors="replace"):
        return []
    return [_finding("repo", repo.name, "no commit-msg hook blocking new AI credit lines",
                     fix_id=f"hook:{repo}", fix="install the hook (an existing hook keeps running first)",
                     level="high")]


def check_files(repo: Path) -> list:
    out = []
    for rel in filter(None, _git(repo, "ls-files", "-z").split("\0")):
        path = repo / rel
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE:
                continue
            hits = findings(_decode(path.read_bytes()))
        except OSError:
            continue
        if hits:
            out.append(_finding("repo", f"{repo.name}/{rel}", _summary(hits),
                                fix="remove the line(s) in a normal commit or PR"))
    return out


def check_history(repo: Path) -> list:
    log = _git(repo, "log", "--all", "--format=%an%x1f%ae%x1f%cn%x1f%ce%x1f%B%x1e")
    bad_msg = bad_id = 0
    for rec in filter(str.strip, log.split("\x1e")):
        parts = rec.strip("\n").split("\x1f", 4)
        if len(parts) < 5:
            continue
        an, ae, cn, ce, body = parts
        bad_id += identity(an, ae) or identity(cn, ce)
        bad_msg += bool(findings(body))
    out = []
    if bad_msg:
        out.append(_finding("history", repo.name, f"{bad_msg} past commit message(s) carry an AI credit line",
                            fix="leave as is: rewriting pushed history breaks every clone", level="info"))
    if bad_id:
        out.append(_finding("history", repo.name, f"{bad_id} past commit(s) authored under an AI identity",
                            fix="leave as is; check your git user.name and user.email", level="info"))
    return out


def check_project_settings(repo: Path) -> list:
    out = []
    for f in sorted((repo / ".claude").glob("settings*.json")):
        data = _json(f)
        if not isinstance(data, dict):
            continue
        att = data.get("attribution")
        if data.get("includeCoAuthoredBy") is True or (isinstance(att, dict) and (att.get("commit") or att.get("pr"))):
            out.append(_finding("repo", f"{repo.name}/.claude/{f.name}", "project setting turns AI attribution on",
                                fix="set attribution commit and pr to \"\" in a PR", level="high"))
    return out


def check_records(repo: Path) -> list:
    out = []
    names = {p.name.upper() for p in repo.iterdir()} if repo.is_dir() else set()
    if not any(n.startswith(("LICENSE", "LICENCE", "COPYING")) for n in names):
        out.append(_finding("repo", repo.name, "no LICENSE file naming you as the copyright holder",
                            fix="add one in a PR", level="low"))
    for co in (repo / "CODEOWNERS", repo / ".github" / "CODEOWNERS", repo / "docs" / "CODEOWNERS"):
        if co.is_file():
            for i, line in enumerate(co.read_text(errors="replace").splitlines(), 1):
                for who in re.findall(r"@[\w./\[\]-]+", line):
                    if AI_IDENTITY.search(who.lstrip("@").split("/")[-1]):
                        out.append(_finding("repo", f"{repo.name}/{co.relative_to(repo)}",
                                            f"AI identity listed as code owner at line {i}", fix="remove it in a PR"))
    return out


def scan_repo(repo: Path) -> list:
    return (check_hook(repo) + check_files(repo) + check_history(repo) + check_project_settings(repo)
            + check_records(repo))


def check_github(clones: list) -> list:
    who = _run(["gh", "api", "user", "--jq", ".login"])
    if who.returncode != 0 or not who.stdout.strip():
        return [_finding("github", "GitHub", "gh is not signed in or offline, so GitHub repos were not listed",
                         fix="run gh auth login, then scan again", level="info")]
    user = who.stdout.strip()
    r = _run(["gh", "repo", "list", user, "--limit", "500", "--json", "name,isArchived,isFork,licenseInfo"])
    if r.returncode != 0:
        return [_finding("github", user, "could not list GitHub repos", level="info")]
    local = set()
    for repo in clones:
        m = re.search(rf"{re.escape(user.lower())}/([\w.-]+?)(\.git)?$",
                      _git(repo, "remote", "get-url", "origin").strip().lower())
        if m:
            local.add(m.group(1))
    out = []
    for item in json.loads(r.stdout or "[]"):
        if item.get("isArchived") or item.get("isFork"):
            continue
        name = item["name"]
        if name.lower() not in local:
            out.append(_finding("github", f"{user}/{name}", "no local clone, so its files and history were not "
                                "scanned", fix="clone it, then scan again", level="info"))
        if not item.get("licenseInfo"):
            out.append(_finding("github", f"{user}/{name}", "GitHub shows no licence", fix="add one in a PR",
                                level="low"))
    return out


# ---------- AI tools ----------

RULE_HEAD = "## Authorship (your-authorship-skill)"
# A rule the user already wrote counts too: a heading named Ownership or Authorship.
OWN_RULE = re.compile(r"^#{1,6}\s*(ownership|authorship)\b", re.I | re.M)


def rule_text(owner: str) -> str:
    return (f"{RULE_HEAD}\n\nEverything in these projects is owned and authored by {owner}. You are a tool, not an "
            "author. Never add a co-author trailer, a generated-with footer, a session link or any credit line "
            "naming an AI to a commit, PR, tag, release or file.\n")


def check_claude() -> list:
    d = home() / ".claude"
    if not d.is_dir():
        return []
    out = []
    data = _json(d / "settings.json")
    att = data.get("attribution") if isinstance(data, dict) else None
    ok = isinstance(att, dict) and att.get("commit") == "" and att.get("pr") == "" and att.get("sessionUrl") is False
    if not ok:
        out.append(_finding("tool", "Claude Code ~/.claude/settings.json",
                            "attribution not fully off (needs commit \"\", pr \"\", sessionUrl false)",
                            fix_id="claude-attribution", fix="set attribution commit/pr empty, sessionUrl false",
                            level="high"))
    out += _rule_file_check("Claude Code", d / "CLAUDE.md", "claude-md")
    return out


def _rule_file_check(tool: str, path: Path, fix_id: str) -> list:
    text = path.read_text(errors="replace") if path.is_file() else ""
    if RULE_HEAD in text or OWN_RULE.search(text):
        return []
    return [_finding("tool", f"{tool} ~/{path.relative_to(home())}", "no authorship rule in its global instructions",
                     fix_id=fix_id, fix="append the authorship rule block (backup kept)")]


def check_codex() -> list:
    d = home() / ".codex"
    if not d.is_dir():
        return []
    out = _rule_file_check("Codex", d / "AGENTS.md", "codex-agents")
    cfg = d / "config.toml"
    text = cfg.read_text(errors="replace") if cfg.is_file() else ""
    if re.search(r'^\s*commit_attribution\s*=\s*"[^"]+"', text, re.M):
        out.append(_finding("tool", "Codex ~/.codex/config.toml", "commit_attribution names an author label",
                            fix='set commit_attribution = "" by hand', level="high"))
    out.append(_finding("tool", "Codex (account setting)", "some Codex builds decide commit attribution per account; "
                        "no local key turns it off", fix="keep the commit-msg hook installed in each repo",
                        level="info"))
    return out


def check_cursor() -> list:
    d = home() / ".cursor"
    if not d.is_dir():
        return []
    out = []
    data = _json(d / "cli-config.json")
    att = data.get("attribution") if isinstance(data, dict) else None
    if not (isinstance(att, dict) and att.get("attributeCommitsToAgent") is False):
        out.append(_finding("tool", "Cursor CLI ~/.cursor/cli-config.json", "agent commit attribution not off",
                            fix_id="cursor-cli", fix="set attribution.attributeCommitsToAgent false", level="high"))
    out.append(_finding("tool", "Cursor app", "commit and PR attribution toggles live in the app UI",
                        fix="Cursor Settings > Agent > Attribution: turn both off", level="info"))
    return out


def check_gemini() -> list:
    d = home() / ".gemini"
    return _rule_file_check("Gemini CLI", d / "GEMINI.md", "gemini-md") if d.is_dir() else []


def check_git_identity() -> list:
    name = _git(home(), "config", "--global", "user.name").strip()
    email = _git(home(), "config", "--global", "user.email").strip()
    if not name or not email:
        return [_finding("tool", "git ~/.gitconfig", "global user.name or user.email is not set",
                         fix="git config --global user.name/user.email with your own identity", level="medium")]
    if identity(name, email):
        return [_finding("tool", "git ~/.gitconfig", "global git identity is an AI identity",
                         fix="set user.name and user.email to your own", level="high")]
    return []


# ---------- report ----------

ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


def scan(github=True, repos=None) -> list:
    clones = local_repos() if repos is None else repos
    out = check_git_identity() + check_claude() + check_codex() + check_cursor() + check_gemini()
    for repo in clones:
        out += scan_repo(repo)
    if github:
        out += check_github(clones)
    return sorted(out, key=lambda f: (ORDER[f["level"]], f["area"], f["target"]))


def render(found: list, repos: int, owner: str) -> str:
    counts = {k: sum(f["level"] == k for f in found) for k in ORDER}
    lines = [f"# Authorship sweep {time.strftime('%Y-%m-%d %H:%M')}", "",
             f"Owner: {owner}. {repos} local repo(s) scanned. " +
             ", ".join(f"{v} {k}" for k, v in counts.items()) + ".", "",
             "| # | Level | Area | Target | Finding | Fix | Fix ID |", "|---|---|---|---|---|---|---|"]
    for i, f in enumerate(found, 1):
        cells = [str(i), f["level"], f["area"], f["target"], f["problem"], f["fix"], f["fix_id"] or "-"]
        lines.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    return "\n".join(lines) + "\n"


# ---------- fixes ----------

def _backup(path: Path) -> None:
    if path.exists():
        shutil.copy2(path, path.with_name(f"{path.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}"))


def _edit_json(path: Path, change) -> None:
    data = _json(path) if path.exists() else {}
    if not isinstance(data, dict):
        raise SystemExit(f"{path} is not a JSON object; fix it by hand")
    change(data)
    _backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _append_rule(path: Path, owner: str) -> None:
    _backup(path)
    old = path.read_text() if path.is_file() else ""
    sep = ("\n" if old and not old.endswith("\n") else "") + ("\n" if old else "")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(old + sep + rule_text(owner))


def install_hook(repo: Path) -> str:
    d, custom = hooks_dir(repo)
    if d is None:
        raise SystemExit(f"{repo}: core.hooksPath is set ({custom}) or not a git repo; install by hand")
    d.mkdir(parents=True, exist_ok=True)
    dest, local = d / "commit-msg", d / "commit-msg.local"
    note = ""
    if dest.is_file() and HOOK_MARKER not in dest.read_text(errors="replace"):
        if local.exists():
            raise SystemExit(f"{local} already exists; merge {dest} into it by hand, then run again")
        _backup(dest)
        dest.rename(local)
        note = f" (your old hook kept as {local.name} and runs first)"
    elif dest.is_file():
        _backup(dest)
    shutil.copy2(HOOK_SRC, dest)
    dest.chmod(0o755)
    return f"hook installed: {dest}{note}"


def plan_fix(fix_id: str, owner: str):
    h = home()
    if fix_id == "claude-attribution":
        path = h / ".claude" / "settings.json"
        return (f"{path}: attribution = commit \"\", pr \"\", sessionUrl false (backup kept)",
                lambda: _edit_json(path, lambda d: d.update(attribution={"commit": "", "pr": "", "sessionUrl": False})))
    if fix_id == "cursor-cli":
        path = h / ".cursor" / "cli-config.json"

        def change(d):
            att = d.get("attribution") if isinstance(d.get("attribution"), dict) else {}
            att["attributeCommitsToAgent"] = False
            d["attribution"] = att
        return f"{path}: attribution.attributeCommitsToAgent = false (backup kept)", lambda: _edit_json(path, change)
    rule_files = {"claude-md": h / ".claude" / "CLAUDE.md", "codex-agents": h / ".codex" / "AGENTS.md",
                  "gemini-md": h / ".gemini" / "GEMINI.md"}
    if fix_id in rule_files:
        path = rule_files[fix_id]
        return (f"{path}: append the authorship rule naming {owner} (backup kept)",
                lambda: _append_rule(path, owner))
    if fix_id.startswith("hook:"):
        repo = Path(fix_id.split(":", 1)[1]).expanduser()
        if not (repo / ".git").exists():
            return None
        return (f"{repo}: install the commit-msg hook (an existing hook keeps running first)",
                lambda: print(install_hook(repo)))
    return None


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="authorship.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="read-only report")
    s.add_argument("--json", action="store_true")
    s.add_argument("--no-github", action="store_true")
    s.add_argument("--out", help="also write the markdown report to this file")
    s.add_argument("--root", action="append", help="folder holding repos (repeatable); default: common folders")
    s.add_argument("--owner", default="")
    f = sub.add_parser("fix", help="show or apply one fix by its ID")
    f.add_argument("fix_id")
    f.add_argument("--apply", action="store_true", help="make the change (only after the user said yes)")
    f.add_argument("--owner", default="")
    sub.add_parser("message", help="check one commit message file").add_argument("file")
    sub.add_parser("text", help="check stdin")
    a = p.parse_args(argv)
    if a.cmd in ("message", "text"):
        body = Path(a.file).read_text(errors="replace") if a.cmd == "message" else sys.stdin.read()
        hits = findings(body)
        for n, kind in hits:
            print(f"authorship: {kind} at line {n}", file=sys.stderr)
        if hits:
            print("authorship: remove the AI credit line(s); you are the author.", file=sys.stderr)
        return 1 if hits else 0
    owner = owner_name(a.owner)
    if a.cmd == "scan":
        repos = local_repos(a.root)
        found = scan(github=not a.no_github, repos=repos)
        if a.json:
            print(json.dumps(found, indent=2, ensure_ascii=False))
        else:
            report = render(found, len(repos), owner)
            print(report, end="")
            if a.out:
                Path(a.out).write_text(report)
        return 0
    plan = plan_fix(a.fix_id, owner)
    if plan is None:
        print(f"{a.fix_id}: no automatic fix (repo files go through a normal PR; history stays as is)",
              file=sys.stderr)
        return 2
    desc, act = plan
    if not a.apply:
        print(f"would change: {desc}\nrun again with --apply after the user says yes")
        return 0
    act()
    print(f"done: {desc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
