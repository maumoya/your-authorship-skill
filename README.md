<!-- Header: create it with skill-forger-e2e's make_header.sh, then put its img tag here, centered, width 100%. -->

<!-- Regenerate the row with badges.sh: it adds Scorecard, Best Practices and measured benefit badges when they exist. -->
<p align="center">
  <img src="https://img.shields.io/badge/Claude%20Code-skill%20%2B%20plugin-7c5cfc" alt="Claude Code skill and plugin">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license">
  <a href="https://opensource.org/license/mit"><img src="https://img.shields.io/badge/Open%20Source-OSI%20approved%20license-3DA639?logo=opensourceinitiative&logoColor=white" alt="Open Source: OSI-approved MIT license"></a>
  <img src="https://img.shields.io/badge/privacy-no%20tracking%20%C2%B7%20no%20data%20collected-7c5cfc" alt="Privacy: no tracking, no data collected">
  <a href="https://scorecard.dev/viewer/?uri=github.com/maumoya/your-authorship-skill"><img src="https://api.scorecard.dev/projects/github.com/maumoya/your-authorship-skill/badge" alt="OpenSSF Scorecard"></a>
</p>

# Your Authorship Skill

Keeps you the sole author of your code when you build with AI agents: scans every local repo, your GitHub account and your AI tool settings for AI co-author trailers, generated-with footers and credit lines, fixes each one only on your OK, and installs a commit-msg hook so new ones are blocked.

<!-- Put a picture or a ≤10 s GIF here: one input → one result. -->

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

## Use

Type: `TRIGGER ONE`

## How it is tested

`evals/` holds one case per promise. Run `claude plugin eval . --allow-tools`.
Every PR runs `scripts/lint_skill.sh` in CI.

## FAQ

### What does it do?

Keeps you the sole author of your code when you build with AI agents: scans every local repo, your GitHub account and your AI tool settings for AI co-author trailers, generated-with footers and credit lines, fixes each one only on your OK, and installs a commit-msg hook so new ones are blocked.

### Does it send my data anywhere?

No. It is instructions and local scripts only.

<!-- Draft this with skill-forger-e2e's owner_profile.sh, then let the owner edit it. -->
## About the author

Hi, I'm **Mauricio Alonso Moya Tapia** ([@maumoya](https://github.com/maumoya)). I built your-authorship-skill because WHY_YOU_BUILT_IT.

Say hi or follow my work on [GitHub](https://github.com/maumoya).

## License

MIT © 2026 Mauricio Alonso Moya Tapia
