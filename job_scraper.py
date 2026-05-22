"""
job_scraper.py
--------------
Multi-source job discovery from Indeed, LinkedIn, Glassdoor, and generic job boards.

Usage:
    python job_scraper.py \
        --keyword "Business Intelligence" \
        --location "Austin, TX" \
        --sources indeed,linkedin,glassdoor \
        [--output-file jobs.json]

Requirements:
    pip install requests beautifulsoup4 python-dateutil
"""

import argparse
import json
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Generator
from urllib.parse import quote, urlencode

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# User agent to avoid being blocked
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# ─────────────────────────────────────────────
# JOB DATA MODEL
# ─────────────────────────────────────────────

class JobPosting:
    """Normalized job posting from any source."""

    def __init__(
        self,
        title: str,
        company: str,
        location: str,
        url: str,
        source: str,
        posted_date: datetime | None = None,
        description: str = "",
        salary_min: int | None = None,
        salary_max: int | None = None,
        job_type: str = "",  # full-time, contract, etc.
    ):
        self.title = title
        self.company = company
        self.location = location
        self.url = url
        self.source = source  # "indeed", "linkedin", "glassdoor", etc.
        self.posted_date = posted_date or datetime.now()
        self.description = description
        self.salary_min = salary_min
        self.salary_max = salary_max
        self.job_type = job_type
        self.job_id = self._compute_id()

    def _compute_id(self) -> str:
        """Generate unique ID from title, company, location."""
        key = f"{self.title.lower()}_{self.company.lower()}_{self.location.lower()}"
        key = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
        return key

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "url": self.url,
            "source": self.source,
            "posted_date": self.posted_date.isoformat(),
            "description": self.description[:500],  # Truncate for storage
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "job_type": self.job_type,
        }

    @staticmethod
    def from_dict(data: dict) -> "JobPosting":
        """Reconstruct JobPosting from dict."""
        posted_date = None
        if isinstance(data.get("posted_date"), str):
            posted_date = datetime.fromisoformat(data["posted_date"])
        return JobPosting(
            title=data["title"],
            company=data["company"],
            location=data["location"],
            url=data["url"],
            source=data["source"],
            posted_date=posted_date,
            description=data.get("description", ""),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            job_type=data.get("job_type", ""),
        )


# ─────────────────────────────────────────────
# JOB SCRAPERS
# ─────────────────────────────────────────────

class IndeedScraper:
    """Scrape jobs from Indeed.com"""

    BASE_URL = "https://www.indeed.com/jobs"

    def search(
        self, keyword: str, location: str, limit: int = 50
    ) -> Generator[JobPosting, None, None]:
        """Search Indeed for jobs."""
        logger.info(f"Searching Indeed for '{keyword}' in '{location}'")

        start = 0
        fetched = 0

        while fetched < limit:
            params = {
                "q": keyword,
                "l": location,
                "start": start,
                "limit": 50,
                "sort": "date",
            }

            try:
                resp = requests.get(
                    self.BASE_URL,
                    params=params,
                    headers={"User-Agent": USER_AGENT},
                    timeout=10,
                )
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Error fetching Indeed page: {e}")
                break

            soup = BeautifulSoup(resp.content, "html.parser")
            job_cards = soup.find_all("div", class_="job_seen_beacon")

            if not job_cards:
                logger.info("No more jobs found on Indeed")
                break

            for card in job_cards:
                if fetched >= limit:
                    break

                try:
                    job = self._parse_job_card(card)
                    if job:
                        yield job
                        fetched += 1
                except Exception as e:
                    logger.debug(f"Error parsing Indeed job card: {e}")

            start += 50
            time.sleep(1)  # Be respectful

        logger.info(f"Fetched {fetched} jobs from Indeed")

    def _parse_job_card(self, card: BeautifulSoup) -> JobPosting | None:
        """Parse a single Indeed job card."""
        # Title
        title_elem = card.find("h2", class_="jobTitle")
        if not title_elem:
            return None
        title = title_elem.get_text(strip=True)

        # Company
        company_elem = card.find("span", class_="companyName")
        company = company_elem.get_text(strip=True) if company_elem else "Unknown"

        # Location
        location_elem = card.find("div", class_="companyLocation")
        location = location_elem.get_text(strip=True) if location_elem else "Unknown"

        # URL
        link_elem = card.find("a", class_="jcs")
        if not link_elem:
            return None
        url = "https://indeed.com" + link_elem.get("href", "")

        # Posted date
        posted_elem = card.find("span", class_="date")
        posted_date = self._parse_indeed_date(posted_elem.get_text(strip=True) if posted_elem else "")

        # Salary (if available)
        salary_elem = card.find("div", class_="salary-snippet")
        salary_min, salary_max = self._parse_salary(salary_elem.get_text(strip=True) if salary_elem else "")

        return JobPosting(
            title=title,
            company=company,
            location=location,
            url=url,
            source="indeed",
            posted_date=posted_date,
            salary_min=salary_min,
            salary_max=salary_max,
        )

    @staticmethod
    def _parse_indeed_date(date_str: str) -> datetime:
        """Parse 'Posted 2 days ago' style dates."""
        if "ago" in date_str.lower():
            match = re.search(r"(\d+)\s+(day|hour|week)", date_str, re.IGNORECASE)
            if match:
                value, unit = int(match.group(1)), match.group(2).lower()
                delta = {"day": "days", "hour": "hours", "week": "weeks"}.get(unit, "days")
                if delta == "days":
                    return datetime.now() - timedelta(days=value)
                elif delta == "hours":
                    return datetime.now() - timedelta(hours=value)
                elif delta == "weeks":
                    return datetime.now() - timedelta(weeks=value)
        return datetime.now()

    @staticmethod
    def _parse_salary(salary_str: str) -> tuple[int | None, int | None]:
        """Extract salary range from string like '$100,000 - $150,000 a year'"""
        if not salary_str:
            return None, None
        
        numbers = re.findall(r"\$?([\d,]+)", salary_str)
        if len(numbers) >= 2:
            try:
                return int(numbers[0].replace(",", "")), int(numbers[1].replace(",", ""))
            except ValueError:
                pass
        return None, None


class LinkedInScraper:
    """Scrape jobs from LinkedIn (using unofficial API approach)."""

    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/searchWithCurrentFilters"

    def search(
        self, keyword: str, location: str, limit: int = 50
    ) -> Generator[JobPosting, None, None]:
        """Search LinkedIn for jobs."""
        logger.info(f"Searching LinkedIn for '{keyword}' in '{location}'")

        # Note: LinkedIn official API is restricted. This uses the jobs API endpoint.
        # For production, consider using LinkedIn Recruiter Lite or official APIs.

        start = 0
        fetched = 0

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.linkedin.normalized+json+2.1",
        }

        while fetched < limit:
            params = {
                "keywords": keyword,
                "location": location,
                "start": start,
                "count": 25,
            }

            try:
                resp = requests.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers,
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                logger.error(f"Error fetching LinkedIn jobs: {e}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing LinkedIn response: {e}")
                break

            jobs = data.get("elements", [])
            if not jobs:
                logger.info("No more jobs found on LinkedIn")
                break

            for job_data in jobs:
                if fetched >= limit:
                    break

                try:
                    job = self._parse_job_data(job_data)
                    if job:
                        yield job
                        fetched += 1
                except Exception as e:
                    logger.debug(f"Error parsing LinkedIn job: {e}")

            start += 25
            time.sleep(1)

        logger.info(f"Fetched {fetched} jobs from LinkedIn")

    def _parse_job_data(self, job_data: dict) -> JobPosting | None:
        """Parse a LinkedIn job data object."""
        try:
            # Extract nested data
            title = job_data.get("title", "")
            company_name = job_data.get("companyName", "")
            location = job_data.get("location", "")
            job_id = job_data.get("jobId", "")
            posted_date_ms = job_data.get("listedDate", 0)

            if not all([title, company_name, job_id]):
                return None

            url = f"https://www.linkedin.com/jobs/view/{job_id}/"

            posted_date = datetime.fromtimestamp(posted_date_ms / 1000) if posted_date_ms else datetime.now()

            return JobPosting(
                title=title,
                company=company_name,
                location=location,
                url=url,
                source="linkedin",
                posted_date=posted_date,
            )
        except Exception as e:
            logger.debug(f"Error parsing LinkedIn job data: {e}")
            return None


class GlassdoorScraper:
    """Scrape jobs from Glassdoor."""

    BASE_URL = "https://www.glassdoor.com/Job/jobs.htm"

    def search(
        self, keyword: str, location: str, limit: int = 50
    ) -> Generator[JobPosting, None, None]:
        """Search Glassdoor for jobs."""
        logger.info(f"Searching Glassdoor for '{keyword}' in '{location}'")

        params = {
            "keyword": keyword,
            "location": location,
            "p": 1,
        }

        fetched = 0
        page = 1

        while fetched < limit:
            params["p"] = page

            try:
                resp = requests.get(
                    self.BASE_URL,
                    params=params,
                    headers={"User-Agent": USER_AGENT},
                    timeout=10,
                )
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Error fetching Glassdoor page: {e}")
                break

            soup = BeautifulSoup(resp.content, "html.parser")
            job_items = soup.find_all("li", {"data-job-id": True})

            if not job_items:
                logger.info("No more jobs found on Glassdoor")
                break

            for item in job_items:
                if fetched >= limit:
                    break

                try:
                    job = self._parse_job_item(item)
                    if job:
                        yield job
                        fetched += 1
                except Exception as e:
                    logger.debug(f"Error parsing Glassdoor job: {e}")

            page += 1
            time.sleep(1)

        logger.info(f"Fetched {fetched} jobs from Glassdoor")

    def _parse_job_item(self, item: BeautifulSoup) -> JobPosting | None:
        """Parse a single Glassdoor job item."""
        try:
            # Title
            title_elem = item.find("a", class_="jobLink")
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")
            if url and not url.startswith("http"):
                url = "https://www.glassdoor.com" + url

            # Company
            company_elem = item.find("div", class_="employerName")
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"

            # Location
            location_elem = item.find("div", class_="location")
            location = location_elem.get_text(strip=True) if location_elem else "Unknown"

            return JobPosting(
                title=title,
                company=company,
                location=location,
                url=url,
                source="glassdoor",
                posted_date=datetime.now(),
            )
        except Exception as e:
            logger.debug(f"Error parsing Glassdoor item: {e}")
            return None


# ─────────────────────────────────────────────
# JOB STORAGE
# ─────────────────────────────────────────────

class JobDatabase:
    """Simple JSON-based job database."""

    def __init__(self, file_path: Path = Path("data/jobs.json")):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.jobs: dict[str, JobPosting] = self._load()

    def _load(self) -> dict[str, JobPosting]:
        """Load jobs from JSON file."""
        if not self.file_path.exists():
            return {}

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
            return {
                job_id: JobPosting.from_dict(job_data)
                for job_id, job_data in data.items()
            }
        except Exception as e:
            logger.error(f"Error loading jobs database: {e}")
            return {}

    def add_job(self, job: JobPosting) -> bool:
        """Add a job to the database (if not duplicate)."""
        if job.job_id in self.jobs:
            return False  # Already exists
        self.jobs[job.job_id] = job
        return True

    def save(self) -> None:
        """Save jobs to JSON file."""
        data = {
            job_id: job.to_dict()
            for job_id, job in self.jobs.items()
        }
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(data)} jobs to {self.file_path}")

    def get_jobs(self, source: str | None = None) -> list[JobPosting]:
        """Get all jobs, optionally filtered by source."""
        jobs = list(self.jobs.values())
        if source:
            jobs = [j for j in jobs if j.source == source]
        return sorted(jobs, key=lambda j: j.posted_date, reverse=True)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def search_jobs(
    keyword: str,
    location: str,
    sources: list[str] | None = None,
    limit: int = 50,
    output_file: str | None = None,
) -> list[JobPosting]:
    """Search for jobs across multiple sources."""

    if sources is None:
        sources = ["indeed", "linkedin", "glassdoor"]

    db = JobDatabase(Path(output_file) if output_file else Path("data/jobs.json"))
    scrapers = {
        "indeed": IndeedScraper(),
        "linkedin": LinkedInScraper(),
        "glassdoor": GlassdoorScraper(),
    }

    all_jobs = []

    for source in sources:
        if source not in scrapers:
            logger.warning(f"Unknown source: {source}")
            continue

        scraper = scrapers[source]
        new_jobs = 0

        for job in scraper.search(keyword, location, limit // len(sources)):
            if db.add_job(job):
                all_jobs.append(job)
                new_jobs += 1
            else:
                logger.debug(f"Duplicate job: {job.job_id}")

        logger.info(f"Added {new_jobs} new jobs from {source}")

    db.save()
    return all_jobs


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Search for jobs across multiple job boards."
    )
    parser.add_argument(
        "--keyword",
        required=True,
        help='Job keyword, e.g. "Business Intelligence"',
    )
    parser.add_argument(
        "--location",
        required=True,
        help='Location, e.g. "Austin, TX"',
    )
    parser.add_argument(
        "--sources",
        default="indeed,linkedin,glassdoor",
        help="Comma-separated sources: indeed,linkedin,glassdoor",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Total jobs to fetch (default: 50)",
    )
    parser.add_argument(
        "--output-file",
        default="data/jobs.json",
        help="Output JSON file (default: data/jobs.json)",
    )

    args = parser.parse_args()
    sources = [s.strip() for s in args.sources.split(",")]

    jobs = search_jobs(
        keyword=args.keyword,
        location=args.location,
        sources=sources,
        limit=args.limit,
        output_file=args.output_file,
    )

    print(f"\n✅ Found {len(jobs)} new jobs!")
    for job in jobs[:5]:
        print(f"  • {job.title} @ {job.company} ({job.location})")
    if len(jobs) > 5:
        print(f"  ... and {len(jobs) - 5} more")


if __name__ == "__main__":
    main()
