+++
title = "bpf-next llm summaries"
Description = ""
Tags = []
Categories = []
Date = 2026-04-01T00:00:00+00:00
column = "left"
+++

I try to follow the [bpf-next mailing list](https://lore.kernel.org/bpf/) closely, but I always miss things. LWN is incredible, I'm a long time subscriber, but there's still gaps I'd like to fill. So I built a small automated system to summarize the mailing list for me and publish the results [here on my site](/bpf-next/). 

It works in two stages. First, a GitHub Actions workflow runs every morning at 5am ET. It queries the [Patchwork REST API](https://patchwork.kernel.org/api/) for recent bpf-next patches and commits the raw patch data to a staging directory in this blog's [repository](https://github.com/grantseltzer/blog). An hour later at 6am ET, a [Claude Code scheduled agent](https://docs.anthropic.com/en/docs/claude-code/scheduled-agents) picks up the staging files, reads the raw patch data, generates structured JSON summaries, writes them to `data/bpf_next/daily/YYYY-MM-DD.json`, cleans up the staging files, and pushes. That push triggers CI to rebuild and deploy the site to [grantseltzer.github.io](https://github.com/grantseltzer/grantseltzer.github.io). On Mondays the workflow also generates a weekly rollup, and on the 1st of each month a monthly one. Each summary is kept as a dated file so the page serves as a running archive.

Check it out [here](/bpf-next/).