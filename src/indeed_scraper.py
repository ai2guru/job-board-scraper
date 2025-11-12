from __future__ import annotations

import logging
import time
import json
import os
from dataclasses import dataclass
from typing import Iterable, List

import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://www.indeed.com/",
}


def _load_custom_headers() -> dict[str, str]:
    headers = DEFAULT_HEADERS.copy()
    user_agent = os.getenv("INDEED_USER_AGENT")
    if user_agent:
        headers["User-Agent"] = user_agent.strip()

    accept_language = os.getenv("INDEED_ACCEPT_LANGUAGE")
    if accept_language:
        headers["Accept-Language"] = accept_language.strip()

    extra_headers = os.getenv("INDEED_EXTRA_HEADERS")
    if extra_headers:
        try:
            parsed = json.loads(extra_headers)
            if isinstance(parsed, dict):
                headers.update({str(k): str(v) for k, v in parsed.items()})
        except json.JSONDecodeError:
            logging.warning("INDEED_EXTRA_HEADERS is not valid JSON; ignoring.")

    session_cookie = os.getenv("INDEED_SESSION_COOKIE")
    if session_cookie:
        headers["Cookie"] = session_cookie.strip()
    return headers


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=int(os.getenv("INDEED_RETRY_TOTAL", "5")),
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        backoff_factor=float(os.getenv("INDEED_RETRY_BACKOFF", "2")),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.headers.update(_load_custom_headers())
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = _build_session()


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


def fetch_page(url: str, session: requests.Session | None = None) -> BeautifulSoup | None:
    sess = session or SESSION
    try:
        resp = sess.get(url, timeout=20)
        if resp.status_code == 403:
            logging.warning(
                "Indeed returned HTTP 403 for %s. Try adjusting INDEED_USER_AGENT or INDEED_SESSION_COOKIE.",
                url,
            )
            return None
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


def fetch_indeed_jobs(
    keywords: Iterable[str],
    location: str,
    pages_per_keyword: int = 1,
    delay_sec: float = 1.0,
    session: requests.Session | None = None,
) -> List[Job]:
    results: List[Job] = []
    seen_urls: set[str] = set()
    sess = session or SESSION
    for kw in keywords:
        for page in range(pages_per_keyword):
            start = page * 10  # Indeed uses increments of 10 per page
            url = build_search_url(kw, location, start)
            logging.info("Fetching Indeed: %s", url)
            soup = fetch_page(url, session=sess)
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
