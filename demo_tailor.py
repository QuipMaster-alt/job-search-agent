"""
demo_tailor.py
--------------
Demonstrate batch resume tailoring with dry-run (no API calls).
"""

from pathlib import Path
from tailor_resume import tailor_batch

def demo_batch_tailor():
    """Demo batch tailoring from assessments."""
    
    # For this demo, we need a sample CV. Create a minimal one.
    sample_cv = {
        "cv": {
            "sections": {
                "summary": [
                    "Experienced BI and Analytics leader with 15+ years in the field."
                ],
                "experience": [
                    {
                        "company": "Tech Corp",
                        "position": "Senior Director, Analytics",
                        "start_date": "2020-01",
                        "end_date": "present",
                        "highlights": [
                            "Led analytics transformation for 500+ person organization",
                            "Built Tableau-based reporting infrastructure",
                        ]
                    }
                ],
                "skills": [
                    {
                        "label": "Business Intelligence",
                        "details": ["Tableau", "Power BI", "Looker"]
                    },
                    {
                        "label": "Data Platforms",
                        "details": ["Snowflake", "BigQuery", "Redshift"]
                    },
                    {
                        "label": "Analytics",
                        "details": ["SQL", "Python", "Statistics"]
                    }
                ]
            }
        }
    }
    
    # Save sample CV
    import yaml
    cv_path = Path("demo_cv.yaml")
    with open(cv_path, "w") as f:
        yaml.dump(sample_cv, f)
    
    print("🎯 Demo: Batch Resume Tailoring")
    print("=" * 70)
    print(f"\n✓ Created sample CV: {cv_path}")
    print("\n📋 Dry-run: Tailoring top-fit jobs (80+)...\n")
    
    # Run batch tailor in dry-run mode
    results = tailor_batch(
        cv_path=cv_path,
        jobs_file=Path("data/jobs.json"),
        assessments_file=Path("data/assessments.json"),
        min_fit=80,
        output_dir=Path("demo_tailored"),
        dry_run=True,
    )
    
    print(f"\n✅ Demo complete!")
    print(f"\nWith real API key, this would create {len([r for r in results if r])} tailored resumes")
    print(f"\nTo run for real:")
    print(f"  export ANTHROPIC_API_KEY='your-key'")
    print(f"  python tailor_resume.py \\")
    print(f"    --cv demo_cv.yaml \\")
    print(f"    --batch-assess data/assessments.json \\")
    print(f"    --jobs data/jobs.json \\")
    print(f"    --min-fit 80")
    
    # Cleanup
    cv_path.unlink()


if __name__ == "__main__":
    demo_batch_tailor()
