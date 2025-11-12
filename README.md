Job Board Scraper Prototype

Overview
- Scrapes basic job listings from Indeed for hardcoded keywords and location.
- Appends results to a Google Sheet (creates if not present).
- Avoids duplicates by checking existing Job URL values in the sheet.
- Logs to console and logs/scraper.log.

Scope (Prototype)
- One job board: Indeed
- Hardcoded keywords and titles
- Manual execution via CLI (no scheduler yet)

Project Structure
- requirements.txt — Python dependencies
- src/indeed_scraper.py — Indeed fetch and parsing logic
- src/google_sheets.py — Google Sheets auth + helpers
- src/main.py — CLI entrypoint; wiring, dedupe, logging

Prerequisites
1) Python 3.10+
2) Google Cloud service account with Sheets + Drive API access
   - Enable “Google Sheets API” and “Google Drive API” on a GCP project.
   - Create a service account with a JSON key.
   - Share your target spreadsheet with the service account email (Editor).

Credentials
You can supply service account credentials in one of two ways:
- Environment variable: GOOGLE_SERVICE_ACCOUNT_INFO (JSON string)
- File: service_account.json in the repository root

Example (PowerShell):
  $env:GOOGLE_SERVICE_ACCOUNT_INFO = Get-Content -Raw .\service_account.json

OR place service_account.json at the project root.

Installation
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt

Configuration (optional via env vars)
- SHEET_NAME: spreadsheet name (default: Job Scraper Prototype)
- SHEET_TAB: worksheet/tab name (default: Indeed Jobs)
- JOB_LOCATION: Indeed search location (default: United States)
- PAGES_PER_KEYWORD: pages per keyword (default: 1)

Run
  python -m src.main

What gets written
Headers:
- Job Title | Company | Location | Posting Date | Job URL

Notes
- Indeed markup can change; the parser is defensive but may require updates over time.
- This prototype focuses on job scraping and data organization, not contact discovery.
- For contact enrichment (name, title, email), plan to add a follow-up module using company domains and an enrichment API, then merge into the same sheet.

Next Steps (beyond prototype)
- Add scheduler (cron, GitHub Actions, Task Scheduler)
- Expand to additional job boards
- Add company contact discovery + verification
- Improve dedupe (hashing, fuzzy matching)
- Unit tests for parsers

