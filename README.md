# Kanpo daily naturalization notice monitor

This project monitors **public navigation/index metadata** on https://www.kanpo.go.jp/ for headings mentioning `帰化` or `国籍法`. It intentionally does **not** extract, OCR, collect, or retain individuals' personal details from protected notices.

## Set up
1. Create a **private** GitHub repository and upload this folder's contents, including `.github/workflows/daily.yml`.
2. Open GitHub → Actions → Daily Kanpo naturalization notice monitor → Run workflow for an immediate first run.
3. The scheduled workflow runs at 00:00 UTC (09:00 JST) every day. GitHub scheduled workflows may be delayed or occasionally skipped.
4. Open `data/notices.csv` to see any detected index links. Workflow runs also provide a CSV artifact.
5. If GitHub rejects the push, in repository Settings → Actions → General → Workflow permissions, allow read/write, or use a separate pull-request workflow.

## Limitations
- This is a **best-effort metadata monitor**, not an official Kanpo API. The current website's HTML structure is not guaranteed.
- Some notice headings may be present only in PDFs, and the official site deliberately protects certain personal-information notices from extraction. A zero-row day **does not mean** no naturalizations occurred.
- The homepage may show previous dates, and some index links may be missing or inaccessible.
- The script is designed to start with the latest issue at first execution, not to backfill earlier days.
- Respect website access conditions, publication limits, and privacy protections.
- It stores only notice metadata, not people's names, addresses, or birthdates.

## Local execution
```bash
python -m pip install -r requirements.txt
python monitor.py
```
