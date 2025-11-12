import logging
import os
import sys
from pathlib import Path
from typing import List

# Use absolute imports so running via `python -m src.main` works.
from src.google_sheets import open_sheet, ensure_headers
from src.indeed_scraper import fetch_indeed_jobs, jobs_to_rows, job_headers


def setup_logging():
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "scraper.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def read_existing_urls(ws) -> set:
    try:
        data = ws.get_all_records()
        urls = {row.get("Job URL", "") for row in data if row.get("Job URL")}
        return set(urls)
    except Exception:
        logging.exception("Failed reading existing URLs; continuing with empty set")
        return set()


def append_new_rows(ws, headers: List[str], rows: List[List[str]], existing_urls: set):
    # Filter rows by URL dedupe
    url_idx = headers.index("Job URL")
    filtered = [r for r in rows if r[url_idx] not in existing_urls]
    if not filtered:
        logging.info("No new rows to append. Skipping update.")
        return 0

    ws.append_rows(filtered, value_input_option="RAW")
    logging.info("Appended %d new rows.", len(filtered))
    return len(filtered)


def main():
    setup_logging()
    logging.info("Starting job scraper prototype.")

    # Config (prototype: hardcoded)
    spreadsheet_name = os.getenv("SHEET_NAME", "Job Scraper Prototype")
    worksheet_name = os.getenv("SHEET_TAB", "Indeed Jobs")
    keywords = [
        "python developer",
        "data engineer",
        "backend engineer",
    ]
    location = os.getenv("JOB_LOCATION", "United States")
    pages_per_keyword = int(os.getenv("PAGES_PER_KEYWORD", "1"))

    # Open sheet and ensure headers
    try:
        _, ws = open_sheet(spreadsheet_name, worksheet_name)
    except RuntimeError as err:
        logging.critical("%s", err)
        sys.exit(1)
    headers = job_headers()
    ensure_headers(ws, headers)

    # Scrape Indeed
    jobs = fetch_indeed_jobs(keywords, location, pages_per_keyword=pages_per_keyword)
    rows = jobs_to_rows(jobs)
    logging.info("Scraped %d rows from Indeed.", len(rows))

    # Dedupe vs Sheet and append
    existing_urls = read_existing_urls(ws)
    appended = append_new_rows(ws, headers, rows, existing_urls)

    logging.info("Done. New rows appended: %d", appended)


if __name__ == "__main__":
    main()
