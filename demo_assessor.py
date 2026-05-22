"""
demo_assessor.py
----------------
Demo job assessments using simulated Claude responses.
Useful for testing without API calls.
"""

import json
from pathlib import Path
from datetime import datetime
from job_scraper import JobDatabase
from job_assessor import JobAssessment, AssessmentDatabase

# Simulated assessments for demo jobs
MOCK_ASSESSMENTS = {
    "senior_business_intelligence_manager_instructure_austin_tx": {
        "fit_score": 85,
        "salary_assessment": {
            "salary_aligned": True,
            "comment": "Salary $180-220k is within target range"
        },
        "key_skills_match": ["BI leadership", "Austin location", "EdTech market", "Team management"],
        "red_flags": [],
        "pros": ["Perfect role level", "Excellent company culture", "Growth opportunity in EdTech"],
        "cons": ["Highly competitive", "May require relocation to Austin office"],
        "recommendation": "🟢 STRONG FIT — Apply immediately"
    },
    "vp_of_analytics_insights_tableau_software_seattle_wa": {
        "fit_score": 78,
        "salary_assessment": {
            "salary_aligned": True,
            "comment": "Salary $220-280k exceeds target but acceptable for VP role"
        },
        "key_skills_match": ["VP level", "Analytics strategy", "Tableau expertise"],
        "red_flags": ["Seattle location (not Austin)", "Requires relocation"],
        "pros": ["Perfect role level", "Industry leader in analytics tools", "Strategic role"],
        "cons": ["Requires relocation", "Different geographic market"],
        "recommendation": "🟡 CONSIDER — Excellent role but location mismatch"
    },
    "data_analytics_lead_dell_technologies_austin_tx": {
        "fit_score": 72,
        "salary_assessment": {
            "salary_aligned": False,
            "comment": "Salary $160-200k is slightly below target range"
        },
        "key_skills_match": ["Austin location", "Leadership opportunity", "Enterprise scale"],
        "red_flags": ["Below target salary", "Less strategic than director role"],
        "pros": ["Local Austin opportunity", "Large enterprise", "Hybrid flexibility"],
        "cons": ["Salary below target", "More operational than strategic"],
        "recommendation": "🟡 CONSIDER — Good local opportunity but salary lower"
    },
    "director_business_intelligence_tesla_austin_tx": {
        "fit_score": 88,
        "salary_assessment": {
            "salary_aligned": True,
            "comment": "Salary $200-260k is within target and well-aligned"
        },
        "key_skills_match": ["Director level role", "Austin location", "High-growth company", "Data-driven culture"],
        "red_flags": [],
        "pros": ["Perfect role level", "Tesla's analytics maturity", "Competitive salary", "Local Austin position"],
        "cons": ["Highly competitive", "Fast-paced demanding culture"],
        "recommendation": "🟢 STRONG FIT — Excellent match, apply immediately"
    },
    "analytics_engineer_remote_databricks_remote": {
        "fit_score": 65,
        "salary_assessment": {
            "salary_aligned": True,
            "comment": "Salary $170-240k is within range, fully remote"
        },
        "key_skills_match": ["Remote opportunity", "Data engineering background", "Modern data stack"],
        "red_flags": ["More technical/engineering than leadership", "Younger role level"],
        "pros": ["Fully remote", "Industry leader in data analytics", "Competitive salary"],
        "cons": ["Less leadership-oriented", "Different skill focus from BI management"],
        "recommendation": "🟡 CONSIDER — Remote flexibility but less aligned with VP goals"
    },
    "senior_bi_developer_ibm_hybrid_austin_area": {
        "fit_score": 58,
        "salary_assessment": {
            "salary_aligned": False,
            "comment": "Salary $140-180k is below target, more senior developer than leader"
        },
        "key_skills_match": ["Austin area", "Hybrid flexibility"],
        "red_flags": ["Below target salary", "Developer role not leadership", "Mature enterprise tech stack"],
        "pros": ["Hybrid arrangement", "IBM's established analytics practice", "Austin area location"],
        "cons": ["Salary too low", "Less strategic than target role", "More technical than management"],
        "recommendation": "🔴 SKIP — Salary below target and less aligned with leadership goals"
    },
}

def generate_demo_assessments():
    """Generate demo assessments for all jobs in database."""
    
    # Load jobs
    job_db = JobDatabase(Path("data/jobs.json"))
    jobs = job_db.get_jobs()
    
    print(f"📊 Generating assessments for {len(jobs)} jobs...\n")
    
    # Load or create assessments database
    assessment_db = AssessmentDatabase(Path("data/assessments.json"))
    
    # Create assessments
    for job in jobs:
        if job.job_id in MOCK_ASSESSMENTS:
            assessment_data = MOCK_ASSESSMENTS[job.job_id]
            assessment = JobAssessment(
                job_id=job.job_id,
                fit_score=assessment_data["fit_score"],
                salary_assessment=assessment_data["salary_assessment"],
                key_skills_match=assessment_data["key_skills_match"],
                red_flags=assessment_data["red_flags"],
                pros=assessment_data["pros"],
                cons=assessment_data["cons"],
                recommendation=assessment_data["recommendation"],
            )
            assessment_db.add_assessment(assessment)
            print(f"✓ {assessment.recommendation} | {job.title} @ {job.company}")
    
    # Save
    assessment_db.save()
    
    # Print summary
    print(f"\n{'='*70}")
    summary = assessment_db.get_summary()
    print(f"📊 Assessment Summary:")
    print(f"  Total assessed: {summary['total_assessed']}")
    print(f"  Average fit score: {summary['average_fit_score']:.1f}")
    print(f"  🟢 Strong fits (80+): {summary['strong_fits_80_plus']}")
    print(f"  🟡 Good fits (60-79): {summary['good_fits_60_79']}")
    print(f"  🔴 Weak fits (<40): {summary['weak_fits_below_40']}")
    
    print(f"\n🎯 Top Opportunities:")
    strong_fits = assessment_db.get_assessments(min_fit=80)
    for i, assessment in enumerate(strong_fits, 1):
        # Find corresponding job
        job = next((j for j in jobs if j.job_id == assessment.job_id), None)
        if job:
            print(f"  {i}. {job.title} @ {job.company}")
            print(f"     Score: {assessment.fit_score} | {assessment.recommendation}")
            print(f"     Salary: {assessment.salary_assessment['comment']}")
            print()


if __name__ == "__main__":
    generate_demo_assessments()
