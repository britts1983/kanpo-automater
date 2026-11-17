#!/usr/bin/env python3
"""Monitor official Kanpo HTML indexes for naturalization notices (metadata only)."""
import csv
import datetime as dt
import re
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

BASE = 'https://www.kanpo.go.jp/'
OUT = Path('data/notices.csv')
FIELDS = ['first_seen_jst', 'publication_date', 'issue', 'notice_type', 'source_url', 'review_status']
HEADERS = {'User-Agent': 'KanpoNoticeMonitor/2.0 (daily public-index metadata check)'}


def get_html(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    if 'html' not in r.headers.get('Content-Type', '').lower():
        return None
    return BeautifulSoup(r.content, 'html.parser')


def official_link(parent, href):
    url = urljoin(parent, href).split('#', 1)[0]
    p = urlparse(url)
    return url if p.scheme == 'https' and p.netloc == 'www.kanpo.go.jp' else None


def main():
    now = dt.datetime.now(ZoneInfo('Asia/Tokyo'))
    home = get_html(BASE)
    # Only inspect the newest publication date shown on the home page.
    # The old script accidentally picked up 2025-03-31 from the site announcement.
    dates = re.findall(r'令和\s*(\d+)年\s*(\d+)月\s*(\d+)日', home.get_text(' ', strip=True))
    valid = []
    for y, m, d in dates:
        try:
            date = dt.date(2018 + int(y), int(m), int(d))
            if date <= now.date() and date >= now.date() - dt.timedelta(days=90):
                valid.append(date)
        except ValueError:
            continue
    if not valid:
        raise RuntimeError('No recent publication date found; inspect the official homepage')
    published = max(valid)
    stamp = published.strftime('%Y%m%d')
    print('Latest published Kanpo issue:', published)
    if published != now.date():
        print('No issue dated today; inspecting latest published issue only')

    # Date-scoped crawl: do not accidentally add old naturalization notices.
    queue = deque()
    for a in home.select('a[href]'):
        url = official_link(BASE, a['href'])
        if url and stamp in url and not url.lower().endswith(('.pdf', '.jpg', '.png')):
            queue.append((url, 0))
    seen = set()
    notices = {}
    while queue and len(seen) < 60:
        url, depth = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            soup = get_html(url)
        except requests.RequestException as exc:
            print('Could not read:', url, exc)
            continue
        if soup is None:
            continue
        for a in soup.select('a[href]'):
            label = a.get_text(' ', strip=True)
            target = official_link(url, a['href'])
            if not target or stamp not in target:
                continue
            if '帰化' in label or '日本国に帰化を許可する件' in label:
                notices[target] = label[:200] or '日本国に帰化を許可する件'
            elif depth < 2 and not target.lower().endswith(('.pdf', '.jpg', '.png')):
                queue.append((target, depth + 1))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        with OUT.open('r', newline='', encoding='utf-8-sig') as f:
            existing = list(csv.DictReader(f))
    else:
        existing = []
    # Repair dates from the previous buggy run when URL itself provides the date.
    for row in existing:
        match = re.search(r'kanpo\.go\.jp/(20\d{6})/', row.get('source_url', ''))
        if match:
            row['publication_date'] = dt.datetime.strptime(match.group(1), '%Y%m%d').date().isoformat()
    keys = {(r['publication_date'], r['source_url']) for r in existing}
    new = 0
    for url, heading in notices.items():
        key = (published.isoformat(), url)
        if key not in keys:
            existing.append(dict(first_seen_jst=now.isoformat(timespec='seconds'),
                                 publication_date=published.isoformat(), issue=heading,
                                 notice_type='帰化 / naturalization-related', source_url=url,
                                 review_status='manual_review_required'))
            keys.add(key)
            new += 1
    with OUT.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(existing)
    print(f'New notice links: {new}; total stored: {len(existing)}')
    for url, heading in notices.items():
        print(heading, url)
    if not notices:
        print('No naturalization links detected in accessible indexes; this does not prove none were published.')
    print('Individual names are NOT extracted from image-protected notices.')


if __name__ == '__main__':
    main()
