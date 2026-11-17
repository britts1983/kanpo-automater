"""Send a daily Kanpo status email using a Gmail app password stored in GitHub Secrets."""
import csv
import datetime as dt
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

RECIPIENT = os.getenv('EMAIL_TO', 'brittobaby23@gmail.com')
SENDER = os.environ['GMAIL_ADDRESS']
PASSWORD = os.environ['GMAIL_APP_PASSWORD'].replace(' ', '')
TODAY = dt.datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()
FILE = Path('data/notices.csv')

with FILE.open(newline='', encoding='utf-8-sig') as f:
    rows = [r for r in csv.DictReader(f) if r.get('publication_date') == TODAY]

if rows:
    status = 'YES'
    body = f'YES — Naturalization announcement(s) found for {TODAY} (Japan).\n\n'
    for row in rows:
        body += f"Notice: {row.get('issue', '')}\nOfficial link: {row.get('source_url', '')}\n\n"
else:
    status = 'NO'
    body = (f'NO — No naturalization announcement was detected for {TODAY} (Japan) '
            'in the accessible Kanpo indexes. This does not guarantee that none was published.\n'
            'Please check https://www.kanpo.go.jp/ if you need certainty.\n')

body += '\nNote: This monitor tracks official notice links, not individual names.\n'
message = EmailMessage()
message['From'] = SENDER
message['To'] = RECIPIENT
message['Subject'] = f'Kanpo naturalization: {status} — {TODAY}'
message.set_content(body)
with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context(), timeout=30) as smtp:
    smtp.login(SENDER, PASSWORD)
    smtp.send_message(message)
print(f'Sent {status} report for {TODAY} to {RECIPIENT}')
