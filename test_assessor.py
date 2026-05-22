"""
test_assessor.py
----------------
Test job assessor functionality with mock data.
"""

import json
from pathlib import Path
from job_assessor import JobAssessment, AssessmentDatabase

def test_assessment_model():
    """Test JobAssessment model."""
    assessment = JobAssessment(
        job_id="test_job_123",
        fit_score=85,
        salary_assessment={
            "salary_aligned": True,
            "comment": "Salary $200-240k matches target perfectly"
        },
        key_skills_match=["Tableau expert", "Data warehouse", "Team leadership"],
        red_flags=["Requires relocation"],
        pros=["Great company", "Perfect role level", "Growth opportunity"],
        cons=["High travel requirement"],
        recommendation="🟢 STRONG FIT — Apply immediately"
    )
    
    print(f"✓ Created assessment: {assessment.job_id}")
    print(f"  Fit score: {assessment.fit_score}")
    print(f"  Recommendation: {assessment.recommendation}")
    
    # Test serialization
    data = assessment.to_dict()
    assessment2 = JobAssessment.from_dict(data)
    assert assessment2.fit_score == assessment.fit_score
    print(f"✓ Serialization works")


def test_assessment_database():
    """Test assessment database."""
    db_path = Path("test_assessments.json")
    db = AssessmentDatabase(db_path)
    
    # Create mock assessments
    assessments = [
        JobAssessment(
            job_id="strong_fit_001",
            fit_score=88,
            salary_assessment={"salary_aligned": True, "comment": "Perfect salary match"},
            key_skills_match=["Tableau", "SQL", "Leadership"],
            red_flags=[],
            pros=["Great company", "Remote", "Perfect role"],
            cons=["New industry"],
            recommendation="🟢 STRONG FIT — Apply ASAP"
        ),
        JobAssessment(
            job_id="good_fit_001",
            fit_score=72,
            salary_assessment={"salary_aligned": True, "comment": "Slightly above range"},
            key_skills_match=["Power BI", "Data modeling"],
            red_flags=["Requires relocation"],
            pros=["Good company", "Growth", "Leadership role"],
            cons=["No remote", "New tools"],
            recommendation="🟡 CONSIDER — Good opportunity"
        ),
        JobAssessment(
            job_id="weak_fit_001",
            fit_score=35,
            salary_assessment={"salary_aligned": False, "comment": "Below target salary"},
            key_skills_match=[],
            red_flags=["Senior role mismatch", "Wrong industry", "Salary too low"],
            pros=["Flexible hours"],
            cons=["Not a fit", "Low pay"],
            recommendation="🔴 SKIP — Likely mismatch"
        ),
    ]
    
    for assessment in assessments:
        db.add_assessment(assessment)
    
    db.save()
    print(f"✓ Saved {len(db.assessments)} assessments")
    
    # Reload
    db2 = AssessmentDatabase(db_path)
    assert len(db2.assessments) == 3
    print(f"✓ Loaded {len(db2.assessments)} assessments")
    
    # Test filtering
    strong = db2.get_assessments(min_fit=80)
    good = db2.get_assessments(min_fit=60, max_fit=79)
    weak = db2.get_assessments(max_fit=39)
    
    assert len(strong) == 1
    assert len(good) == 1
    assert len(weak) == 1
    print(f"✓ Filtering by fit score works")
    
    # Test summary
    summary = db2.get_summary()
    assert summary["total_assessed"] == 3
    assert summary["strong_fits_80_plus"] == 1
    assert summary["good_fits_60_79"] == 1
    assert summary["weak_fits_below_40"] == 1
    print(f"✓ Summary statistics correct")
    
    print(f"\n📊 Summary:")
    print(f"  Total: {summary['total_assessed']}")
    print(f"  Average fit: {summary['average_fit_score']:.1f}")
    print(f"  Strong fits: {summary['strong_fits_80_plus']}")
    print(f"  Good fits: {summary['good_fits_60_79']}")
    
    # Cleanup
    db_path.unlink()
    print(f"✓ Cleaned up test file")


if __name__ == "__main__":
    print("Testing job_assessor module...\n")
    test_assessment_model()
    print()
    test_assessment_database()
    print("\n✅ All assessor tests passed!")
