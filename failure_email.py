"""Alert on a failed check rather than incorrectly reporting no notices."""
import datetime as dt
import os
import smtplib
import ssl
from email.message import EmailMessage
from zoneinfo import ZoneInfo

today = dt.datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()
msg = EmailMessage()
msg['From'] = os.environ['GMAIL_ADDRESS']
msg['To'] = os.getenv('EMAIL_TO', 'brittobaby23@gmail.com')
msg['Subject'] = f'Kanpo naturalization: CHECK FAILED — {today}'
msg.set_content(f'The Kanpo monitor could not complete its check for {today}. No YES/NO conclusion is available. Please review GitHub Actions logs and https://www.kanpo.go.jp/.')
with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context(), timeout=30) as smtp:
    smtp.login(os.environ['GMAIL_ADDRESS'], os.environ['GMAIL_APP_PASSWORD'].replace(' ', ''))
    smtp.send_message(msg)
print('Failure notification sent')
