+++
title = "Automating bpf-next mailing list summaries"
Description = ""
Tags = []
Categories = []
Date = 2026-04-01T00:00:00+00:00
column = "left"
+++

I try to follow the [bpf-next mailing list](https://lore.kernel.org/bpf/) closely, but I always miss things. LWN is incredible, I'm a long time subscriber, but there's still gaps I'd like to fill. So I built a small automated system to summarize the mailing list for me and publish the results [here on my site](/bpf-next/). 

A GitHub Actions workflow runs every morning at 6am ET on a cron schedule. It fetches the Atom feed from lore.kernel.org directly, parses it, and passes the patch list to the Claude API to generate a structured JSON summary. That JSON gets committed to this blog's [repository](https://github.com/grantseltzer/blog) under `data/bpf_next/daily/YYYY-MM-DD.json`, which triggers a Hugo build and deploy to [grantseltzer.github.io](https://github.com/grantseltzer/grantseltzer.github.io). On Mondays the workflow also generates a weekly rollup, and on the 1st of each month a monthly one. Each summary is kept as a dated file so the page serves as a running archive. The prompt passed to Claude is below.

```
You are generating a {period} summary of the bpf Linux kernel mailing list for the blog at grant.pizza.

Here are the patch submissions from this period ({period_start} to {period_end}):

{entries}

Return ONLY a single valid JSON object — no markdown, no explanation, no code fences. The schema:

{
  "generated_at": "<ISO 8601 UTC timestamp>",
  "period_start": "<YYYY-MM-DD>",
  "period_end": "<YYYY-MM-DD>",
  "patch_count": <total patches listed above>,
  "thread_count": <number of distinct patch series>,
  "top_contributors": ["First Last", ...],
  "key_topics": ["lowercase-tag", ...],
  "overview": "<2-3 sentences for daily, 3-4 for weekly, 4-6 for monthly>",
  "patches": [
    {
      "title": "<subject with [PATCH vN N/M] prefix stripped>",
      "author": "<First Last>",
      "url": "<lore.kernel.org URL from the data above>",
      "summary": "<3-5 sentences: what it does, why it matters, relevant context>",
      "related_links": []
    }
  ]
}

Select 5-10 of the most notable patches (8-12 for weekly, 10-15 for monthly).
- Prefer new features over minor fixes
- Prioritize core areas: verifier, BTF, kfuncs, maps, helpers, XDP, tc, ringbuf
- Prefer cover letters ([PATCH 0/N]) over individual patches in a series
- Aim for variety across subsystems and contributors
- key_topics: short lowercase tags only, e.g. ["verifier", "kfuncs", "XDP", "ringbuf"]
```
