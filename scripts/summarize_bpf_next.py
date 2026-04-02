#!/usr/bin/env python3
"""
Fetches the bpf mailing list Atom feed and generates daily/weekly/monthly
summaries using the Claude API, writing results to data/bpf_next/*.json.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

import anthropic

ATOM_NS = {'atom': 'http://www.w3.org/2005/Atom'}
LORE_BASE = 'https://lore.kernel.org/bpf'
HEADERS = {
    'User-Agent': 'curl/8.0 (grant.pizza bpf-summarizer; https://github.com/grantseltzer/blog)',
    'Accept': 'application/atom+xml,application/xml',
}


def fetch_url(url):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8')


def fetch_patches(days):
    """Fetch [PATCH] entries from the last `days` days, paginating as needed."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    patches = []
    offset = 0

    while True:
        if offset == 0:
            url = f'{LORE_BASE}/new.atom'
        else:
            url = f'{LORE_BASE}/?x=A&o={offset}'

        try:
            xml_text = fetch_url(url)
        except URLError as e:
            print(f'  Warning: failed to fetch {url}: {e}', file=sys.stderr)
            break

        root = ET.fromstring(xml_text)
        entries = root.findall('atom:entry', ATOM_NS)

        if not entries:
            break

        oldest_on_page = None
        for entry in entries:
            updated_str = entry.find('atom:updated', ATOM_NS).text
            updated = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
            oldest_on_page = updated

            if updated < cutoff:
                continue

            title = (entry.find('atom:title', ATOM_NS).text or '').strip()
            if '[PATCH' not in title and '[RFC' not in title:
                continue

            author_el = entry.find('atom:author/atom:name', ATOM_NS)
            author = author_el.text.strip() if author_el is not None else ''
            link_el = entry.find('atom:link', ATOM_NS)
            link = link_el.get('href', '') if link_el is not None else ''

            patches.append({
                'title': title,
                'author': author,
                'url': link,
                'updated': updated_str,
            })

        # Stop paginating if oldest entry on this page is before cutoff
        if oldest_on_page and oldest_on_page < cutoff:
            break

        # Stop if page was short (last page)
        if len(entries) < 200:
            break

        offset += 200
        if len(patches) > 600:
            break

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
            'overview': f'No patches were submitted to the bpf mailing list during this period.',
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

        out_path = os.path.join('data', 'bpf_next', f'{period}.json')
        with open(out_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f'  Wrote {out_path}')


if __name__ == '__main__':
    main()
