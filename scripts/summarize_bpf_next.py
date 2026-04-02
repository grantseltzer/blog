#!/usr/bin/env python3
"""
Fetches bpf mailing list patches via the patchwork.kernel.org REST API
and generates daily/weekly/monthly summaries using the Claude API,
writing results to data/bpf_next/{period}/YYYY-MM-DD.json.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

import anthropic

PATCHWORK_API = 'https://patchwork.kernel.org/api/patches/'
LIST_ID = 'bpf@vger.kernel.org'
HEADERS = {
    'User-Agent': 'grant.pizza/bpf-summarizer (https://github.com/grantseltzer/blog)',
    'Accept': 'application/json',
}


def fetch_url(url):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def lore_url(msgid):
    """Convert a Message-ID to a lore.kernel.org permalink."""
    msgid = msgid.strip('<>')
    return f'https://lore.kernel.org/bpf/{msgid}/'


def fetch_patches(days):
    """Fetch patches from patchwork for the last `days` days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    since = cutoff.strftime('%Y-%m-%dT%H:%M:%SZ')

    patches = []
    url = f'{PATCHWORK_API}?list_id={LIST_ID}&since={since}&order=-date&per_page=100'

    while url:
        try:
            data = fetch_url(url)
        except URLError as e:
            print(f'  Warning: failed to fetch {url}: {e}', file=sys.stderr)
            break

        items = data if isinstance(data, list) else data.get('results', [])
        next_url = None if isinstance(data, list) else data.get('next')

        for patch in items:
            msgid = patch.get('msgid', '')
            patches.append({
                'title': patch.get('name', '').strip(),
                'author': patch.get('submitter', {}).get('name', '').strip(),
                'url': lore_url(msgid) if msgid else patch.get('web_url', ''),
                'date': patch.get('date', ''),
                'series': patch.get('series', []),
            })

        url = next_url

    return patches


def generate_summary(client, patches, period, period_start, period_end):
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    if not patches:
        return {
            'generated_at': now_str,
            'period_start': period_start,
            'period_end': period_end,
            'patch_count': 0,
            'thread_count': 0,
            'top_contributors': [],
            'key_topics': [],
            'overview': 'No patches were submitted to the bpf mailing list during this period.',
            'patches': [],
        }

    patch_count_hint = {'daily': '5-10', 'weekly': '8-12', 'monthly': '10-15'}[period]
    overview_hint = {'daily': '2-3', 'weekly': '3-4', 'monthly': '4-6'}[period]

    prompt = f"""You are generating a {period} summary of the bpf Linux kernel mailing list for the blog at grant.pizza.

Here are the patch submissions from this period ({period_start} to {period_end}):

{json.dumps(patches[:150], indent=2)}

Return ONLY a single valid JSON object — no markdown, no explanation, no code fences. The schema:

{{
  "generated_at": "{now_str}",
  "period_start": "{period_start}",
  "period_end": "{period_end}",
  "patch_count": <total patches listed above>,
  "thread_count": <number of distinct patch series>,
  "top_contributors": ["First Last", ...],
  "key_topics": ["lowercase-tag", ...],
  "overview": "<{overview_hint} sentences summarizing the period's activity and themes>",
  "patches": [
    {{
      "title": "<subject with [PATCH vN N/M] prefix stripped>",
      "author": "<First Last>",
      "url": "<lore.kernel.org URL from the data above>",
      "summary": "<3-5 sentences: what it does, why it matters, relevant context>",
      "related_links": []
    }}
  ]
}}

Select {patch_count_hint} of the most notable patches.
- Prefer new features over minor fixes
- Prioritize core areas: verifier, BTF, kfuncs, maps, helpers, XDP, tc, ringbuf
- Prefer cover letters ([PATCH 0/N]) over individual patches in a series
- Aim for variety across subsystems and contributors
- key_topics: short lowercase tags only, e.g. ["verifier", "kfuncs", "XDP", "ringbuf"]
"""

    message = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=4096,
        messages=[{'role': 'user', 'content': prompt}],
    )

    return json.loads(message.content[0].text.strip())


def main():
    client = anthropic.Anthropic()
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')

    jobs = [('daily', 1, (now - timedelta(days=1)).strftime('%Y-%m-%d'), today)]

    if now.weekday() == 0:  # Monday
        jobs.append(('weekly', 7, (now - timedelta(days=7)).strftime('%Y-%m-%d'), today))

    if now.day == 1:  # 1st of month
        jobs.append(('monthly', 30, (now - timedelta(days=30)).strftime('%Y-%m-%d'), today))

    for period, days, period_start, period_end in jobs:
        print(f'Generating {period} summary ({period_start} to {period_end})...')
        patches = fetch_patches(days)
        print(f'  Found {len(patches)} patches')

        summary = generate_summary(client, patches, period, period_start, period_end)

        out_path = os.path.join('data', 'bpf_next', period, f'{period_end}.json')
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f'  Wrote {out_path}')


if __name__ == '__main__':
    main()
