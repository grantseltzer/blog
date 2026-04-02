#!/usr/bin/env python3
"""
Fetches bpf mailing list patches via the patchwork.kernel.org REST API
and writes raw patch data to data/bpf_next/staging/ for later summarization
by a Claude Code scheduled agent.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError

PATCHWORK_API = 'https://patchwork.kernel.org/api/patches/'
PROJECT = 'netdevbpf'
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
    since = cutoff.strftime('%Y-%m-%d')

    patches = []
    params = urlencode({'project': PROJECT, 'q': 'bpf-next', 'since': since, 'order': '-date', 'per_page': 100})
    url = f'{PATCHWORK_API}?{params}'

    while url:
        try:
            data = fetch_url(url)
        except URLError as e:
            print(f'  Warning: failed to fetch {url}: {e}', file=sys.stderr)
            break

        items = data if isinstance(data, list) else data.get('results', [])
        next_url = None if isinstance(data, list) else data.get('next')

        for patch in items:
            title = patch.get('name', '').strip()
            msgid = patch.get('msgid', '')
            patches.append({
                'title': title,
                'author': patch.get('submitter', {}).get('name', '').strip(),
                'url': lore_url(msgid) if msgid else patch.get('web_url', ''),
                'date': patch.get('date', ''),
                'series': patch.get('series', []),
            })

        url = next_url

    return patches


def main():
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')
    staging_dir = os.path.join('data', 'bpf_next', 'staging')
    os.makedirs(staging_dir, exist_ok=True)

    jobs = [('daily', 1, (now - timedelta(days=1)).strftime('%Y-%m-%d'), today)]

    if now.weekday() == 0:  # Monday
        jobs.append(('weekly', 7, (now - timedelta(days=7)).strftime('%Y-%m-%d'), today))

    if now.day == 1:  # 1st of month
        jobs.append(('monthly', 30, (now - timedelta(days=30)).strftime('%Y-%m-%d'), today))

    for period, days, period_start, period_end in jobs:
        print(f'Fetching patches for {period} summary ({period_start} to {period_end})...')
        patches = fetch_patches(days)
        print(f'  Found {len(patches)} patches')

        staging_file = os.path.join(staging_dir, f'{period}_{period_end}.json')
        staging_data = {
            'period': period,
            'period_start': period_start,
            'period_end': period_end,
            'fetched_at': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'patches': patches,
        }
        with open(staging_file, 'w') as f:
            json.dump(staging_data, f, indent=2)
        print(f'  Wrote {staging_file}')


if __name__ == '__main__':
    main()
