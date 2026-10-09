# Project rules

## About this project
This project is a new, empty repository with no source files yet, so there is no language, framework or tooling to describe. Update this section once the first code is added.

## Git workflow
- Never commit or push directly to main.
- Before starting a new change, switch to main and pull the latest changes.
- Create a new branch for each change, named like feature/short-description or fix/short-description.
- Write short, clear commit messages that say what changed and why.
- When a change is finished, commit it and push the branch right away. Don't wait for me to ask.
- After pushing, open a pull request with gh pr create and give me the link.
- If a pull request is already open for this branch, just push the new commits to it instead of opening a new one.
- Never merge pull requests yourself. I review and merge them on GitHub.

## Security
- This repository is public. Anyone can read everything in it.
- Before every commit, check the changes for passwords, API keys, tokens or other secrets. If you find any, stop and tell me.
- Never commit .env files. Make sure .env is listed in .gitignore.
