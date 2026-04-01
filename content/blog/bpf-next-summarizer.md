+++
title = "Automating bpf-next mailing list summaries"
Description = ""
Tags = []
Categories = []
Date = 2026-04-01T00:00:00+00:00
column = "left"
+++

I try to follow the [bpf-next mailing list](https://lore.kernel.org/bpf/) closely, but it's so terse sometimes that I always miss things. LWN is incredible, I'm a long time subscriber, but there's still gaps I'd like to fill. So I built a small automated system to summarize the mailing list for me and publish the results [here on my site](/bpf-next/). It's a pretty 'lightweight' setup. A Claude agent runs every morning at 6am, fetches the Atom feed from lore.kernel.org, picks out the most notable patches, writes a structured JSON summary, and pushes it to this blog's [repository](https://github.com/grantseltzer/blog). On Mondays it also generates a weekly rollup, and on the 1st of each month a monthly one. The full prompt given to the agent is below.

```
You are generating summaries of the bpf-next Linux kernel mailing list for the blog at grant.pizza.

You always generate a daily summary. You also check whether to generate a weekly summary (if today is Monday) and a monthly summary (if today is the 1st of the month).

## Step 1 — Determine the date and which summaries to generate

Run `date -u +%Y-%m-%d` to get today's date.
Run `date -u +%u` to get the day of week (1=Monday).
Run `date -u +%d` to get the day of month.

Always generate: daily summary (last 24 hours)
Also generate if day-of-week == 1: weekly summary (last 7 days)
Also generate if day-of-month == 01: monthly summary (last 30 days)

## Step 2 — Fetch patches for each required window

The bpf mailing list is archived at https://lore.kernel.org/bpf/
Fetch the Atom feed: https://lore.kernel.org/bpf/new.atom

For windows longer than 24 hours, paginate by appending ?o=N (e.g. ?o=200, ?o=400) until the full window is covered.

For each window:
- Filter entries whose <updated> timestamp falls within the window
- Focus on patch submissions: subject lines containing [PATCH] or [RFC PATCH]
- Ignore replies, reviews, CI bot messages, and pull request notifications
- For each patch you select, fetch its full lore.kernel.org page to read the commit message body

## Step 3 — Select notable patches per window

Daily: 5–10 patches
Weekly: 8–12 patches
Monthly: 10–15 patches

Prefer:
- New features or subsystem additions over minor fixes
- Core areas: verifier, BTF, kfuncs, maps, helpers, XDP, tc, ringbuf
- Patch series cover letters ([PATCH 0/N]) when available
- Variety across subsystems and contributors
- For weekly/monthly: patches that sparked significant review discussion or multiple revisions

## Step 4 — Find related reading

For each selected patch, search the web for relevant context:
- https://docs.kernel.org/bpf/ — kernel BPF documentation
- https://lwn.net — articles on the topic
- https://grant.pizza — the blog author's own posts on related topics
- https://ebpf.io and https://docs.ebpf.io

Only include links you have verified exist and are genuinely relevant. Empty related_links arrays are fine.

## Step 5 — Write the JSON files

For each summary you are generating, write the corresponding file.

JSON schema (same for all three):
{
  "generated_at": "<ISO 8601 UTC timestamp>",
  "period_start": "<YYYY-MM-DD>",
  "period_end": "<YYYY-MM-DD>",
  "patch_count": <integer>,
  "thread_count": <integer>,
  "top_contributors": ["First Last", ...],
  "key_topics": ["lowercase-tag", ...],
  "overview": "<summary of activity: 2-3 sentences for daily, 3-4 for weekly, 4-6 for monthly>",
  "patches": [
    {
      "title": "<subject with [PATCH vN N/M] prefix stripped>",
      "author": "<First Last>",
      "url": "<full https://lore.kernel.org/bpf/... permalink>",
      "summary": "<3-5 sentences: what it does, why it matters, relevant context>",
      "related_links": [
        {"title": "<descriptive title>", "url": "<https://...>"}
      ]
    }
  ]
}

File paths:
- Daily:   data/bpf_next/daily.json
- Weekly:  data/bpf_next/weekly.json
- Monthly: data/bpf_next/monthly.json

## Step 6 — Commit and push

  git config user.email "bpf-summarizer@grant.pizza"
  git config user.name "bpf-summarizer"
  git add data/bpf_next/daily.json
  # also stage weekly.json and/or monthly.json if generated
  git commit -m "bpf-next summaries $(date -u +%Y-%m-%d)"
  git push origin master
```
