#!/usr/bin/env python3
"""Daily metadata-only Kanpo naturalization notice monitor."""
import csv
import datetime as dt
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE = 'https://www.kanpo.go.jp/'
OUT = Path('data/notices.csv')
FIELDS = ['first_seen_jst','publication_date','issue','notice_type','source_url','review_status']
KEYWORDS = ('帰化', '国籍法')
HEADERS = {'User-Agent': 'KanpoNoticeMonitor/1.0 (metadata-only; once-daily)'}


def fetch(url):
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    return response


def main():
    now = dt.datetime.now(ZoneInfo('Asia/Tokyo'))
    soup = BeautifulSoup(fetch(BASE).content, 'html.parser')
    # Restrict monitoring to the publication date displayed for the current issue.
    page_text = soup.get_text(' ', strip=True)
    m = re.search(r'令和\s*(\d+)年\s*(\d+)月\s*(\d+)日', page_text)
    if not m:
        raise RuntimeError('Cannot determine current publication date; site structure may have changed')
    pubdate = dt.date(2018 + int(m[1]), int(m[2]), int(m[3]))
    if pubdate > now.date():
        raise RuntimeError('Publication date appears to be in the future')
    # Site may show the latest previous working day's issue on weekends/holidays.
    print(f'Latest Kanpo publication: {pubdate}')
    # Collect only navigation / index pages. No PDF text extraction or OCR.
    candidates = []
    for a in soup.select('a[href]'):
        label = a.get_text(' ', strip=True)
        href = urljoin(BASE, a['href'])
        parsed = urlparse(href)
        if parsed.netloc != 'www.kanpo.go.jp' or parsed.scheme != 'https':
            continue
        if any(k in label for k in KEYWORDS):
            candidates.append(('Naturalization-related index link', label, href))
        elif ('目次' in label or '全体目次' in label) and not href.lower().endswith('.pdf'):
            candidates.append(('Index', label, href))
    # Index pages can contain notice headings, without exposing protected PDF content.
    records = []
    visited = set()
    for kind, label, url in candidates[:15]:
        if url in visited:
            continue
        visited.add(url)
        if kind != 'Index':
            records.append((label, url))
            continue
        try:
            sub = BeautifulSoup(fetch(url).content, 'html.parser')
            for a in sub.select('a[href]'):
                heading = a.get_text(' ', strip=True)
                if any(k in heading for k in KEYWORDS):
                    target = urljoin(url, a['href'])
                    if urlparse(target).netloc == 'www.kanpo.go.jp':
                        records.append((heading, target))
        except requests.RequestException as e:
            print(f'Index temporarily unavailable: {url}: {e}')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if OUT.exists():
        with OUT.open(newline='', encoding='utf-8-sig') as f:
            existing = list(csv.DictReader(f))
    known = {(r['publication_date'], r['source_url']) for r in existing}
    new = 0
    for heading, url in records:
        key = (pubdate.isoformat(), url)
        if key in known:
            continue
        issue = heading[:150]
        existing.append(dict(first_seen_jst=now.isoformat(timespec='seconds'),
                             publication_date=pubdate.isoformat(), issue=issue,
                             notice_type='帰化 / naturalization-related', source_url=url,
                             review_status='manual_review_required'))
        known.add(key)
        new += 1
    with OUT.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(existing)
    print(f'New notice links: {new}; total tracked: {len(existing)}')
    if not records:
        print('No naturalization notice links found in accessible HTML indexes. This is NOT proof that no naturalizations were published.')


if __name__ == '__main__':
    main()
