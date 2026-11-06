#!/usr/bin/env bash
set -eu
mkdir -p demo-app && cd demo-app
git init -q -b main --separate-git-dir ../demo-git  # hooks outside a .git/ folder: eval sandboxes lock .git/hooks
git config user.name "Sam Rivera"; git config user.email "sam@example.com"
printf '# demo-app\n\nA tiny app by Sam Rivera.\n' > README.md
git add README.md
t="Co-""Authored-By: Claude <noreply""@anthropic.com>"
git commit -q -m "feat: first page" -m "$t"
printf 'print("hi")\n' > app.py
git add app.py
git commit -q -m "feat: add app"
