"""
demo_jobs.py
------------
Generate demo job data for testing and development.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from job_scraper import JobPosting, JobDatabase

def create_demo_jobs():
    """Create sample job postings for demonstration."""
    
    demo_jobs = [
        JobPosting(
            title="Senior Business Intelligence Manager",
            company="Instructure",
            location="Austin, TX",
            url="https://www.instructure.com/careers/jobs/123",
            source="indeed",
            posted_date=datetime.now() - timedelta(days=2),
            salary_min=180000,
            salary_max=220000,
            job_type="full-time",
        ),
        JobPosting(
            title="VP of Analytics & Insights",
            company="Tableau Software",
            location="Seattle, WA",
            url="https://www.tableau.com/careers/jobs/456",
            source="linkedin",
            posted_date=datetime.now() - timedelta(days=5),
            salary_min=220000,
            salary_max=280000,
            job_type="full-time",
        ),
        JobPosting(
            title="Data Analytics Lead",
            company="Dell Technologies",
            location="Austin, TX",
            url="https://www.dell.com/careers/jobs/789",
            source="glassdoor",
            posted_date=datetime.now() - timedelta(days=1),
            salary_min=160000,
            salary_max=200000,
            job_type="full-time",
        ),
        JobPosting(
            title="Director, Business Intelligence",
            company="Tesla",
            location="Austin, TX",
            url="https://www.tesla.com/careers/jobs/101",
            source="indeed",
            posted_date=datetime.now() - timedelta(days=3),
            salary_min=200000,
            salary_max=260000,
            job_type="full-time",
        ),
        JobPosting(
            title="Analytics Engineer (Remote)",
            company="Databricks",
            location="Remote",
            url="https://www.databricks.com/careers/jobs/202",
            source="linkedin",
            posted_date=datetime.now() - timedelta(days=4),
            salary_min=170000,
            salary_max=240000,
            job_type="full-time",
        ),
        JobPosting(
            title="Senior BI Developer",
            company="IBM",
            location="Hybrid - Austin area",
            url="https://www.ibm.com/careers/jobs/303",
            source="glassdoor",
            posted_date=datetime.now() - timedelta(days=2),
            salary_min=140000,
            salary_max=180000,
            job_type="full-time",
        ),
    ]

    db = JobDatabase(Path("data/jobs.json"))
    
    for job in demo_jobs:
        if db.add_job(job):
            print(f"✓ Added: {job.title} @ {job.company}")
        else:
            print(f"⊘ Skipped (duplicate): {job.title}")
    
    db.save()
    print(f"\n✅ Saved {len(db.jobs)} jobs to data/jobs.json")
    
    # Print summary
    print(f"\n📊 Job Summary:")
    for source in ["indeed", "linkedin", "glassdoor"]:
        jobs = db.get_jobs(source)
        if jobs:
            print(f"  {source.capitalize()}: {len(jobs)} jobs")
    
    print(f"\n💰 Salary Range:")
    salaries = [j.salary_max for j in db.jobs.values() if j.salary_max]
    if salaries:
        print(f"  Minimum: ${min(salaries):,}")
        print(f"  Maximum: ${max(salaries):,}")
        print(f"  Average: ${sum(salaries)//len(salaries):,}")

if __name__ == "__main__":
    create_demo_jobs()
