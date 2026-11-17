# Kanpo daily email monitor

Runs on GitHub Actions at **09:00 JST** (scheduled GitHub jobs can be delayed). It checks accessible Kanpo indexes for naturalization notices, stores source links in `data/notices.csv`, and emails `brittobaby23@gmail.com` every day with YES, NO, or CHECK FAILED.

**Important:** The monitor does **not** extract individual names. `NO` means no notice was detected by the index scraper, not proof that no notice exists. It may miss announcements if the official site changes its HTML structure. The script inspects the latest issue; the email reports only notices whose publication date is *today*. On non-publication days, the result is usually NO.

## Installation

1. Copy `monitor.py`, `email_report.py`, `failure_email.py`, `requirements.txt`, and `.github/workflows/daily.yml` into your existing GitHub repo, preserving the `.github/workflows` path.
2. In the Google account that will send the emails, enable 2-Step Verification and create a **Google App Password** (if available to your account). Never put this password into code or chat.
3. GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `GMAIL_ADDRESS` = the Gmail address that will send the mail (can be the recipient address).
   - `GMAIL_APP_PASSWORD` = the 16-character Google App Password.
4. Commit and push files to `main`.
5. GitHub → **Actions → Daily Kanpo naturalization email → Run workflow**. Verify the email arrives, and check spam if needed.

The workflow uses `00:00 UTC` for `09:00 JST` and attempts to run every day. GitHub may delay or skip scheduled runs. The default branch must contain the workflow and Actions must be enabled. If a Gmail App Password is unavailable, use another SMTP provider or a transactional email service instead.
