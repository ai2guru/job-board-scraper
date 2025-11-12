from __future__ import annotations

import logging
import time
from dataclasses import dataclass, asdict
from typing import Iterable, List, Dict

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class Job:
    title: str
    company: str
    location: str
    date: str
    url: str


def _safe_text(el) -> str:
    return el.get_text(strip=True) if el else ""


def build_search_url(keyword: str, location: str, start: int = 0) -> str:
    # Indeed public search
    return (
        f"https://www.indeed.com/jobs?q={requests.utils.quote(keyword)}"
        f"&l={requests.utils.quote(location)}&start={start}"
    )


def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logging.exception("Failed to fetch %s: %s", url, e)
        return None


def parse_jobs(soup: BeautifulSoup) -> List[Job]:
    jobs: List[Job] = []
    # Indeed markup changes; try common containers
    cards = soup.select("div.job_seen_beacon")
    for card in cards:
        # Title and URL
        a = card.select_one("h2 a") or card.select_one("a.jcs-JobTitle")
        if not a:
            continue
        url = a.get("href") or ""
        if url and url.startswith("/"):
            url = "https://www.indeed.com" + url

        title = a.get("aria-label") or _safe_text(a)

        # Company
        company_el = card.select_one("span.companyName")
        company = _safe_text(company_el)

        # Location
        loc_el = card.select_one("div.companyLocation")
        location = _safe_text(loc_el)

        # Date
        date_el = (
            card.select_one("span.date")
            or card.select_one("span[data-testid='myJobsStateDate']")
            or card.select_one("span[aria-label*='date']")
        )
        date = _safe_text(date_el)

        if url:
            jobs.append(Job(title=title, company=company, location=location, date=date, url=url))
    return jobs


def fetch_indeed_jobs(keywords: Iterable[str], location: str, pages_per_keyword: int = 1, delay_sec: float = 1.0) -> List[Job]:
    results: List[Job] = []
    seen_urls: set[str] = set()
    for kw in keywords:
        for page in range(pages_per_keyword):
            start = page * 10  # Indeed uses increments of 10 per page
            url = build_search_url(kw, location, start)
            logging.info("Fetching Indeed: %s", url)
            soup = fetch_page(url)
            if not soup:
                continue
            jobs = parse_jobs(soup)
            for job in jobs:
                if job.url not in seen_urls:
                    seen_urls.add(job.url)
                    results.append(job)
            time.sleep(delay_sec)
    return results


def jobs_to_rows(jobs: Iterable[Job]) -> List[List[str]]:
    return [[j.title, j.company, j.location, j.date, j.url] for j in jobs]


def job_headers() -> List[str]:
    return ["Job Title", "Company", "Location", "Posting Date", "Job URL"]

