---
title: RunsOnMine upload
emoji: 📊
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
short_description: Receives servebench results and opens a GitHub PR.
---

# RunsOnMine upload service

Receives a result from `servebench submit --upload`, validates it with the same checks as CI, and
opens a pull request on https://github.com/Prajwal7-2002/runsonmine. Nothing is stored here.

Space secrets: `GITHUB_TOKEN` (fine-grained, RunsOnMine repo only: Contents and Pull requests
read/write). Optional variable: `RUNSONMINE_REPO`.
