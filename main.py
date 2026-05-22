"""
main.py
-------
Unified orchestrator for the complete job search agent.

Discover jobs → Assess fit → Tailor resumes → Generate reports

Usage:
    python main.py \
        --keyword "Business Intelligence" \
        --location "Austin, TX" \
        --cv Luis_CV.yaml \
        [--sources indeed,linkedin,glassdoor] \
        [--min-fit 80] \
        [--tailor-resumes]

Environment:
    ANTHROPIC_API_KEY  — for job assessment and resume tailoring
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from job_scraper import search_jobs, JobDatabase
from job_assessor import assess_jobs, AssessmentDatabase
from report_assessments import (
    generate_text_report,
    generate_html_report,
    generate_json_report,
)
from tailor_resume import tailor_batch

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)


class JobSearchAgent:
    """Orchestrates the complete job search workflow."""

    def __init__(
        self,
        keyword: str,
        location: str,
        cv_path: Optional[Path] = None,
        output_dir: Path = Path("search_results"),
        sources: list[str] = None,
    ):
        self.keyword = keyword
        self.location = location
        self.cv_path = cv_path
        self.output_dir = output_dir
        self.sources = sources or ["indeed", "linkedin", "glassdoor"]
        
        self.jobs_file = output_dir / "jobs.json"
        self.assessments_file = output_dir / "assessments.json"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\n🔍 Job Search Agent")
        logger.info(f"{'='*70}")
        logger.info(f"Keyword:    {keyword}")
        logger.info(f"Location:   {location}")
        logger.info(f"Sources:    {', '.join(sources)}")
        if cv_path:
            logger.info(f"CV:         {cv_path}")
        logger.info(f"Output:     {output_dir}")
        logger.info(f"{'='*70}\n")

    def discover_jobs(self, limit: int = 50) -> int:
        """Phase 1: Discover jobs from multiple sources."""
        logger.info(f"📍 PHASE 1: Job Discovery")
        logger.info(f"-" * 70)
        
        # If jobs already exist, skip discovery
        if self.jobs_file.exists():
            db = JobDatabase(self.jobs_file)
            count = len(db.jobs)
            logger.info(f"Using existing {count} jobs from {self.jobs_file}")
            return count
        
        logger.info(f"Searching {', '.join(self.sources)} for jobs...\n")
        
        new_jobs = search_jobs(
            keyword=self.keyword,
            location=self.location,
            sources=self.sources,
            limit=limit,
            output_file=str(self.jobs_file),
        )
        
        logger.info(f"\n✅ Discovered {len(new_jobs)} jobs\n")
        return len(new_jobs)

    def assess_jobs(self, profile_context: Optional[str] = None) -> int:
        """Phase 2: Assess job fit using Claude."""
        logger.info(f"🤖 PHASE 2: Job Assessment")
        logger.info(f"-" * 70)
        
        if not self.jobs_file.exists():
            logger.error("❌ No jobs to assess. Run discovery first.")
            return 0
        
        # Check for API key
        if not os.environ.get("ANTHROPIC_API_KEY"):
            logger.warning("⚠️  ANTHROPIC_API_KEY not set. Skipping assessment.")
            logger.info("   Set API key: export ANTHROPIC_API_KEY='sk-ant-...'")
            return 0
        
        logger.info(f"Assessing jobs for fit...\n")
        
        assessment_db = assess_jobs(
            jobs_file=str(self.jobs_file),
            profile_context=profile_context,
            output_file=str(self.assessments_file),
        )
        
        summary = assessment_db.get_summary()
        logger.info(f"\n✅ Assessment Summary:")
        logger.info(f"   Total: {summary['total_assessed']}")
        logger.info(f"   Avg fit: {summary['average_fit_score']:.1f}")
        logger.info(f"   🟢 Strong (80+): {summary['strong_fits_80_plus']}")
        logger.info(f"   🟡 Good (60-79): {summary['good_fits_60_79']}")
        logger.info(f"   🔴 Weak (<60): {summary['weak_fits_below_40']}\n")
        
        return summary['total_assessed']

    def tailor_resumes(self, min_fit: int = 80) -> int:
        """Phase 3: Tailor resumes for strong-fit jobs."""
        logger.info(f"📝 PHASE 3: Resume Tailoring")
        logger.info(f"-" * 70)
        
        if not self.cv_path:
            logger.warning("⚠️  No CV provided (--cv). Skipping resume tailoring.")
            return 0
        
        if not self.cv_path.exists():
            logger.error(f"❌ CV file not found: {self.cv_path}")
            return 0
        
        if not self.assessments_file.exists():
            logger.warning("⚠️  No assessments found. Run assessment first.")
            return 0
        
        # Check for API key
        if not os.environ.get("ANTHROPIC_API_KEY"):
            logger.warning("⚠️  ANTHROPIC_API_KEY not set. Skipping tailoring.")
            return 0
        
        logger.info(f"Tailoring resumes for jobs with fit ≥ {min_fit}...\n")
        
        tailored_dir = self.output_dir / "tailored_resumes"
        results = tailor_batch(
            cv_path=self.cv_path,
            jobs_file=self.jobs_file,
            assessments_file=self.assessments_file,
            min_fit=min_fit,
            output_dir=tailored_dir,
        )
        
        logger.info(f"\n✅ Tailored {len(results)} resumes\n")
        return len(results)

    def generate_reports(self) -> dict:
        """Phase 4: Generate comprehensive reports."""
        logger.info(f"📊 PHASE 4: Reporting")
        logger.info(f"-" * 70)
        
        if not self.jobs_file.exists() or not self.assessments_file.exists():
            logger.warning("⚠️  Missing jobs or assessments. Skipping reports.")
            return {}
        
        job_db = JobDatabase(self.jobs_file)
        assessment_db = AssessmentDatabase(self.assessments_file)
        
        # Text report
        text_report = generate_text_report(job_db, assessment_db)
        text_path = self.output_dir / "report.txt"
        text_path.write_text(text_report)
        logger.info(f"✅ Text report: {text_path.name}")
        
        # HTML report
        html_report = generate_html_report(job_db, assessment_db)
        html_path = self.output_dir / "report.html"
        html_path.write_text(html_report)
        logger.info(f"✅ HTML report: {html_path.name}")
        
        # JSON report
        json_data = generate_json_report(job_db, assessment_db)
        json_path = self.output_dir / "report.json"
        json_path.write_text(json.dumps(json_data, indent=2))
        logger.info(f"✅ JSON report: {json_path.name}")
        return {
            "text": str(text_path),
            "html": str(html_path),
            "json": str(json_path),
        }

    def run(
        self,
        discover: bool = True,
        assess: bool = True,
        tailor: bool = False,
        report: bool = True,
        limit: int = 50,
        min_fit: int = 80,
        profile_context: Optional[str] = None,
    ) -> dict:
        """Run the complete workflow."""
        results = {
            "jobs_discovered": 0,
            "jobs_assessed": 0,
            "resumes_tailored": 0,
            "reports_generated": {},
        }
        
        try:
            # Phase 1: Discovery
            if discover:
                results["jobs_discovered"] = self.discover_jobs(limit=limit)
            
            # Phase 2: Assessment
            if assess:
                results["jobs_assessed"] = self.assess_jobs(profile_context)
            
            # Phase 3: Tailoring
            if tailor:
                results["resumes_tailored"] = self.tailor_resumes(min_fit)
            
            # Phase 4: Reporting
            if report:
                results["reports_generated"] = self.generate_reports()
            
            # Summary
            logger.info(f"{'='*70}")
            logger.info(f"✅ Job Search Complete!")
            logger.info(f"{'='*70}")
            logger.info(f"Jobs discovered:   {results['jobs_discovered']}")
            logger.info(f"Jobs assessed:     {results['jobs_assessed']}")
            logger.info(f"Resumes tailored:  {results['resumes_tailored']}")
            logger.info(f"\n📁 Results saved to: {self.output_dir}\n")
            
            if results["reports_generated"]:
                logger.info(f"📊 Reports:")
                logger.info(f"   Open HTML: {results['reports_generated'].get('html')}")
            
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Interrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="🔍 Unified Job Search Agent - Discover, Assess, Tailor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Discover and assess jobs
  python main.py --keyword "Business Intelligence" --location "Austin, TX"

  # Full workflow with resume tailoring
  python main.py \\
    --keyword "BI Director" \\
    --location "Austin, TX" \\
    --cv Luis_CV.yaml \\
    --tailor-resumes

  # Use existing jobs, just assess and tailor
  python main.py \\
    --keyword "BI" \\
    --location "Austin, TX" \\
    --cv Luis_CV.yaml \\
    --no-discover \\
    --tailor-resumes

  # Demo mode (no API calls)
  python main.py \\
    --keyword "BI" \\
    --location "Austin, TX" \\
    --demo
        """
    )
    
    # Required args
    parser.add_argument(
        "--keyword",
        required=True,
        help='Job keyword (e.g., "Business Intelligence")'
    )
    parser.add_argument(
        "--location",
        required=True,
        help='Location (e.g., "Austin, TX")'
    )
    
    # Optional args
    parser.add_argument(
        "--cv",
        type=Path,
        help="Path to master RenderCV YAML for tailoring"
    )
    parser.add_argument(
        "--sources",
        default="indeed,linkedin,glassdoor",
        help="Comma-separated job sources (default: indeed,linkedin,glassdoor)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max jobs to discover (default: 50)"
    )
    parser.add_argument(
        "--min-fit",
        type=int,
        default=80,
        help="Min fit score for tailoring (default: 80)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="search_results",
        help="Output directory (default: search_results)"
    )
    
    # Workflow control
    parser.add_argument(
        "--no-discover",
        action="store_true",
        help="Skip job discovery (use existing jobs)"
    )
    parser.add_argument(
        "--no-assess",
        action="store_true",
        help="Skip assessment (requires ANTHROPIC_API_KEY)"
    )
    parser.add_argument(
        "--tailor-resumes",
        action="store_true",
        help="Tailor resumes for strong-fit jobs (requires --cv and API key)"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip report generation"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Demo mode (uses mock data, no API calls)"
    )
    
    args = parser.parse_args()
    
    # Parse sources
    sources = [s.strip() for s in args.sources.split(",")]
    
    # Create agent
    agent = JobSearchAgent(
        keyword=args.keyword,
        location=args.location,
        cv_path=args.cv,
        output_dir=args.output_dir,
        sources=sources,
    )
    
    # Demo mode
    if args.demo:
        logger.warning("⚠️  DEMO MODE - Using mock data, no API calls")
        agent.output_dir = Path("demo_search_results")
        agent.jobs_file = agent.output_dir / "jobs.json"
        agent.assessments_file = agent.output_dir / "assessments.json"
        
        # Copy demo data
        demo_jobs = Path("data/jobs.json")
        demo_assessments = Path("data/assessments.json")
        if demo_jobs.exists():
            import shutil
            agent.output_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(demo_jobs, agent.jobs_file)
            shutil.copy(demo_assessments, agent.assessments_file)
            logger.info("Using demo data from data/\n")
    
    # Run workflow
    agent.run(
        discover=not args.no_discover,
        assess=not args.no_assess,
        tailor=args.tailor_resumes,
        report=not args.no_report,
        limit=args.limit,
        min_fit=args.min_fit,
    )


if __name__ == "__main__":
    main()
