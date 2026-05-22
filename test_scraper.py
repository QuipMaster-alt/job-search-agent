"""
test_scraper.py
---------------
Quick test of the job scraper functionality.
"""

from job_scraper import JobPosting, IndeedScraper, JobDatabase
from pathlib import Path

def test_job_posting():
    """Test JobPosting model."""
    job = JobPosting(
        title="Senior Business Intelligence",
        company="Acme Corp",
        location="Austin, TX",
        url="https://example.com/job/123",
        source="indeed",
        salary_min=180000,
        salary_max=240000,
    )
    
    print(f"✓ Created job: {job.title} @ {job.company}")
    print(f"  ID: {job.job_id}")
    print(f"  Salary: ${job.salary_min:,} - ${job.salary_max:,}")
    
    # Test serialization
    data = job.to_dict()
    job2 = JobPosting.from_dict(data)
    assert job2.title == job.title
    print(f"✓ Serialization works")


def test_job_database():
    """Test job database."""
    db_path = Path("test_jobs.json")
    db = JobDatabase(db_path)
    
    job1 = JobPosting(
        title="Senior BI Engineer",
        company="Tech Corp",
        location="Austin, TX",
        url="https://example.com/1",
        source="indeed",
    )
    
    job2 = JobPosting(
        title="Data Analytics Lead",
        company="StartUp Inc",
        location="Remote",
        url="https://example.com/2",
        source="linkedin",
    )
    
    assert db.add_job(job1) == True
    assert db.add_job(job2) == True
    assert db.add_job(job1) == False  # Duplicate
    
    db.save()
    print(f"✓ Saved {len(db.jobs)} jobs to {db_path}")
    
    # Reload
    db2 = JobDatabase(db_path)
    assert len(db2.jobs) == 2
    print(f"✓ Loaded {len(db2.jobs)} jobs from {db_path}")
    
    # Test filtering
    indeed_jobs = db2.get_jobs("indeed")
    linkedin_jobs = db2.get_jobs("linkedin")
    assert len(indeed_jobs) == 1
    assert len(linkedin_jobs) == 1
    print(f"✓ Filtering by source works")
    
    # Cleanup
    db_path.unlink()
    print(f"✓ Cleaned up test file")


if __name__ == "__main__":
    print("Testing job_scraper module...\n")
    test_job_posting()
    print()
    test_job_database()
    print("\n✅ All tests passed!")
