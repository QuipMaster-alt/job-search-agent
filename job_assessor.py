"""
job_assessor.py
---------------
Assess job fit, salary, and red flags using Claude API.

Usage:
    python job_assessor.py \
        --jobs data/jobs.json \
        --profile-context "BI leader with 15+ years..." \
        [--output assessments.json]

Requirements:
    pip install anthropic pyyaml
    export ANTHROPIC_API_KEY="sk-ant-..."
"""

import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import anthropic

from job_scraper import JobDatabase, JobPosting

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default profile context (can be overridden)
DEFAULT_PROFILE_CONTEXT = """
Candidate: BI and Analytics Leader
- 15+ years experience in Business Intelligence and Data Analytics
- Targeting Director / Senior Director / VP level roles
- Based in Austin, TX (open to remote or hybrid)
- Core tools: Tableau, Power BI, Snowflake, SQL, DAX
- Sweet-spot industries: tech, SaaS, education, healthcare, operations
- Target compensation: $180k–$240k
- Strong SQL, dimensional modeling, and data warehouse expertise
- Experience leading teams and mentoring analysts
- Interested in: analytics strategy, data-driven culture, thought leadership
"""

ASSESSMENT_PROMPT = """
You are an expert career coach assessing job fit for a candidate.

## Candidate Profile
{profile_context}

## Job Posting
Title: {title}
Company: {company}
Location: {location}
URL: {url}

## Task
Analyze this job posting against the candidate's profile. Return a JSON object with:

1. **fit_score** (0-100): Overall fit percentage based on skills, seniority, and industry match
   - 80+: Excellent fit, apply immediately
   - 60-79: Good fit, strong consideration
   - 40-59: Moderate fit, consider if target role
   - 20-39: Weak fit, possible stepping stone
   - Below 20: Poor fit, likely mismatch

2. **salary_assessment**: Object with:
   - salary_aligned (true/false): Does salary match target $180k-$240k range?
   - comment (string): Brief salary assessment

3. **key_skills_match** (array): 3-5 skills/experiences that strongly match (or don't match)

4. **red_flags** (array): Any concerns or mismatches (e.g., required 20+ years, skill gaps, wrong industry)

5. **pros** (array): 3-4 reasons this could be a great fit

6. **cons** (array): 3-4 reasons this might not be ideal

7. **recommendation** (string): One-sentence summary. Start with one of:
   - "🟢 STRONG FIT" — Apply ASAP
   - "🟡 CONSIDER" — Good opportunity if interested
   - "🔴 SKIP" — Likely not a match

Return ONLY valid JSON. No markdown, no explanation.

Example format:
{{
  "fit_score": 82,
  "salary_assessment": {{
    "salary_aligned": true,
    "comment": "Salary range $200-250k is above target but acceptable"
  }},
  "key_skills_match": ["Tableau expert", "Data warehouse design", "Team leadership"],
  "red_flags": ["Requires on-site presence 3 days/week"],
  "pros": ["Perfect seniority level", "Strong company culture", "Growth opportunity"],
  "cons": ["Hybrid arrangement may be challenging", "New industry (fintech)"],
  "recommendation": "🟡 CONSIDER — Strong fit but requires hybrid arrangement"
}}
"""

# ─────────────────────────────────────────────
# ASSESSMENT MODEL
# ─────────────────────────────────────────────

class JobAssessment:
    """Assessment results for a job posting."""

    def __init__(
        self,
        job_id: str,
        fit_score: int,
        salary_assessment: dict[str, Any],
        key_skills_match: list[str],
        red_flags: list[str],
        pros: list[str],
        cons: list[str],
        recommendation: str,
    ):
        self.job_id = job_id
        self.fit_score = fit_score
        self.salary_assessment = salary_assessment
        self.key_skills_match = key_skills_match
        self.red_flags = red_flags
        self.pros = pros
        self.cons = cons
        self.recommendation = recommendation

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "fit_score": self.fit_score,
            "salary_assessment": self.salary_assessment,
            "key_skills_match": self.key_skills_match,
            "red_flags": self.red_flags,
            "pros": self.pros,
            "cons": self.cons,
            "recommendation": self.recommendation,
        }

    @staticmethod
    def from_dict(data: dict) -> "JobAssessment":
        return JobAssessment(
            job_id=data["job_id"],
            fit_score=data["fit_score"],
            salary_assessment=data["salary_assessment"],
            key_skills_match=data["key_skills_match"],
            red_flags=data["red_flags"],
            pros=data["pros"],
            cons=data["cons"],
            recommendation=data["recommendation"],
        )


# ─────────────────────────────────────────────
# ASSESSOR
# ─────────────────────────────────────────────

class JobAssessor:
    """Use Claude to assess job fit."""

    def __init__(
        self,
        profile_context: str = DEFAULT_PROFILE_CONTEXT,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.profile_context = profile_context
        self.model = model
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def assess(self, job: JobPosting) -> JobAssessment | None:
        """Assess a single job posting."""
        logger.info(f"Assessing: {job.title} @ {job.company}")

        prompt = ASSESSMENT_PROMPT.format(
            profile_context=self.profile_context,
            title=job.title,
            company=job.company,
            location=job.location,
            url=job.url,
        )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = message.content[0].text

            # Parse JSON response
            data = self._parse_json(response_text)
            if not data:
                logger.error(f"Failed to parse Claude response for {job.job_id}")
                return None

            assessment = JobAssessment(
                job_id=job.job_id,
                fit_score=data.get("fit_score", 0),
                salary_assessment=data.get("salary_assessment", {}),
                key_skills_match=data.get("key_skills_match", []),
                red_flags=data.get("red_flags", []),
                pros=data.get("pros", []),
                cons=data.get("cons", []),
                recommendation=data.get("recommendation", ""),
            )

            logger.info(f"✓ Fit score: {assessment.fit_score} | {assessment.recommendation}")
            return assessment

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            return None

    @staticmethod
    def _parse_json(response: str) -> dict | None:
        """Extract and parse JSON from Claude response."""
        try:
            # Try direct parse first
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to extract raw JSON object
        match = re.search(r"(\{.*\})", response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        return None


# ─────────────────────────────────────────────
# ASSESSMENT DATABASE
# ─────────────────────────────────────────────

class AssessmentDatabase:
    """Store and retrieve job assessments."""

    def __init__(self, file_path: Path = Path("data/assessments.json")):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.assessments: dict[str, JobAssessment] = self._load()

    def _load(self) -> dict[str, JobAssessment]:
        """Load assessments from JSON file."""
        if not self.file_path.exists():
            return {}

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
            return {
                job_id: JobAssessment.from_dict(assessment)
                for job_id, assessment in data.items()
            }
        except Exception as e:
            logger.error(f"Error loading assessments: {e}")
            return {}

    def add_assessment(self, assessment: JobAssessment) -> None:
        """Add or update an assessment."""
        self.assessments[assessment.job_id] = assessment

    def save(self) -> None:
        """Save assessments to JSON file."""
        data = {
            job_id: assessment.to_dict()
            for job_id, assessment in self.assessments.items()
        }
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(data)} assessments to {self.file_path}")

    def get_assessments(self, min_fit: int = 0, max_fit: int = 100) -> list[JobAssessment]:
        """Get assessments filtered by fit score range."""
        assessments = list(self.assessments.values())
        assessments = [
            a for a in assessments
            if min_fit <= a.fit_score <= max_fit
        ]
        return sorted(assessments, key=lambda a: a.fit_score, reverse=True)

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        assessments = list(self.assessments.values())
        if not assessments:
            return {}

        fit_scores = [a.fit_score for a in assessments]
        strong_fits = [a for a in assessments if a.fit_score >= 80]
        good_fits = [a for a in assessments if 60 <= a.fit_score < 80]
        weak_fits = [a for a in assessments if a.fit_score < 40]

        return {
            "total_assessed": len(assessments),
            "average_fit_score": sum(fit_scores) / len(fit_scores),
            "strong_fits_80_plus": len(strong_fits),
            "good_fits_60_79": len(good_fits),
            "weak_fits_below_40": len(weak_fits),
            "top_3_opportunities": [a.to_dict() for a in strong_fits[:3]],
        }


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def assess_jobs(
    jobs_file: str = "data/jobs.json",
    profile_context: str | None = None,
    output_file: str = "data/assessments.json",
    limit: int | None = None,
) -> AssessmentDatabase:
    """Assess all jobs in the database."""

    if profile_context is None:
        profile_context = DEFAULT_PROFILE_CONTEXT

    # Load jobs
    job_db = JobDatabase(Path(jobs_file))
    jobs = job_db.get_jobs()

    if limit:
        jobs = jobs[:limit]

    if not jobs:
        logger.warning("No jobs found to assess")
        return AssessmentDatabase(Path(output_file))

    logger.info(f"Assessing {len(jobs)} jobs...")

    # Create assessor
    assessor = JobAssessor(profile_context=profile_context)

    # Load existing assessments
    assessment_db = AssessmentDatabase(Path(output_file))

    # Assess each job
    assessed = 0
    for job in jobs:
        if job.job_id in assessment_db.assessments:
            logger.debug(f"⊘ Already assessed: {job.title}")
            continue

        assessment = assessor.assess(job)
        if assessment:
            assessment_db.add_assessment(assessment)
            assessed += 1
        else:
            logger.error(f"Failed to assess: {job.title}")

    assessment_db.save()
    logger.info(f"Assessed {assessed} new jobs")

    return assessment_db


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Assess job fit using Claude AI."
    )
    parser.add_argument(
        "--jobs",
        default="data/jobs.json",
        help="Path to jobs database (default: data/jobs.json)",
    )
    parser.add_argument(
        "--profile-context",
        help="Custom profile context (overrides default)",
    )
    parser.add_argument(
        "--output",
        default="data/assessments.json",
        help="Output assessments file (default: data/assessments.json)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of jobs to assess",
    )

    args = parser.parse_args()

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.error("❌ ANTHROPIC_API_KEY not set. Please set it as an environment variable.")
        exit(1)

    # Assess jobs
    assessment_db = assess_jobs(
        jobs_file=args.jobs,
        profile_context=args.profile_context,
        output_file=args.output,
        limit=args.limit,
    )

    # Print summary
    summary = assessment_db.get_summary()
    if summary:
        print(f"\n📊 Assessment Summary:")
        print(f"  Total assessed: {summary['total_assessed']}")
        print(f"  Average fit score: {summary['average_fit_score']:.1f}")
        print(f"  🟢 Strong fits (80+): {summary['strong_fits_80_plus']}")
        print(f"  🟡 Good fits (60-79): {summary['good_fits_60_79']}")
        print(f"  🔴 Weak fits (<40): {summary['weak_fits_below_40']}")

        if summary.get("top_3_opportunities"):
            print(f"\n🎯 Top Opportunities:")
            for i, opp in enumerate(summary["top_3_opportunities"], 1):
                print(f"  {i}. {opp['recommendation']} (Score: {opp['fit_score']})")


if __name__ == "__main__":
    main()
