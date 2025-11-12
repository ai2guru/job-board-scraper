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
  python -m pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt

Configuration (optional via env vars)
- SHEET_NAME: spreadsheet name (default: Job Scraper Prototype)
- SHEET_TAB: worksheet/tab name (default: Indeed Jobs)
- JOB_LOCATION: Indeed search location (default: United States)
- PAGES_PER_KEYWORD: pages per keyword (default: 1)
- INDEED_USER_AGENT: override the default desktop Chrome UA to reduce blocking
- INDEED_ACCEPT_LANGUAGE: override Accept-Language header (default: en-US,en;q=0.9)
- INDEED_EXTRA_HEADERS: JSON dict merged into the request headers (e.g. {"sec-ch-ua-platform": "\"Windows\""})
- INDEED_SESSION_COOKIE: raw cookie string copied from a valid Indeed browser session
- INDEED_RETRY_TOTAL: retry attempts for transient HTTP errors (default: 3)
- INDEED_RETRY_BACKOFF: seconds for exponential backoff between retries (default: 1)

Run
  python -m src.main

What gets written
Headers:
- Job Title | Company | Location | Posting Date | Job URL

Notes
- Indeed markup can change; the parser is defensive but may require updates over time.
- If Indeed begins returning HTTP 403, set INDEED_USER_AGENT (or INDEED_SESSION_COOKIE / INDEED_EXTRA_HEADERS) with values copied from a working browser session and rerun.
- This prototype focuses on job scraping and data organization, not contact discovery.
- For contact enrichment (name, title, email), plan to add a follow-up module using company domains and an enrichment API, then merge into the same sheet.

Troubleshooting installs (Windows / Python 3.12+)
- If you saw an error about pandas build dependencies (e.g., oldest-supported-numpy markers), upgrade tooling first:
  - python -m pip install --upgrade pip setuptools wheel
- The project now pins pandas to 2.2.3, which has wheels for Python 3.12. If you still get build attempts, try forcing wheels:
  - pip install --only-binary=:all: pandas==2.2.3

Next Steps (beyond prototype)
- Add scheduler (cron, GitHub Actions, Task Scheduler)
- Expand to additional job boards
- Add company contact discovery + verification
- Improve dedupe (hashing, fuzzy matching)
- Unit tests for parsers
