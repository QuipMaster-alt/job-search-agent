"""
report_assessments.py
---------------------
Generate detailed reports from job assessments.

Usage:
    python report_assessments.py \
        --assessments data/assessments.json \
        --jobs data/jobs.json \
        [--format html|json|text]
"""

import argparse
import json
from pathlib import Path
from typing import Any

from job_scraper import JobDatabase
from job_assessor import AssessmentDatabase


def generate_text_report(
    jobs_db: JobDatabase,
    assessments_db: AssessmentDatabase,
) -> str:
    """Generate a text format report."""
    
    jobs = {job.job_id: job for job in jobs_db.get_jobs()}
    assessments = assessments_db.get_assessments()
    summary = assessments_db.get_summary()
    
    lines = []
    lines.append("=" * 80)
    lines.append("JOB ASSESSMENT REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    # Summary section
    lines.append("📊 SUMMARY STATISTICS")
    lines.append("-" * 80)
    lines.append(f"Total Jobs Assessed:        {summary['total_assessed']}")
    lines.append(f"Average Fit Score:          {summary['average_fit_score']:.1f}/100")
    lines.append(f"🟢 Strong Fits (80+):       {summary['strong_fits_80_plus']} jobs")
    lines.append(f"🟡 Good Fits (60-79):       {summary['good_fits_60_79']} jobs")
    lines.append(f"🔴 Weak Fits (<40):         {summary['weak_fits_below_40']} jobs")
    lines.append("")
    
    # Strong fits section
    strong_fits = assessments_db.get_assessments(min_fit=80)
    if strong_fits:
        lines.append("🟢 STRONG FITS (APPLY IMMEDIATELY)")
        lines.append("-" * 80)
        for assessment in strong_fits:
            job = jobs.get(assessment.job_id)
            if job:
                lines.append(f"\n{assessment.fit_score}% — {job.title}")
                lines.append(f"     Company: {job.company}")
                lines.append(f"     Location: {job.location}")
                lines.append(f"     {assessment.recommendation}")
                lines.append(f"     Salary: {assessment.salary_assessment.get('comment', 'N/A')}")
                if assessment.key_skills_match:
                    lines.append(f"     Skills: {', '.join(assessment.key_skills_match[:3])}")
        lines.append("")
    
    # Good fits section
    good_fits = assessments_db.get_assessments(min_fit=60, max_fit=79)
    if good_fits:
        lines.append("🟡 GOOD FITS (CONSIDER)")
        lines.append("-" * 80)
        for assessment in good_fits:
            job = jobs.get(assessment.job_id)
            if job:
                lines.append(f"\n{assessment.fit_score}% — {job.title}")
                lines.append(f"     Company: {job.company}")
                lines.append(f"     Location: {job.location}")
                if assessment.red_flags:
                    lines.append(f"     ⚠️  {assessment.red_flags[0]}")
                if assessment.pros:
                    lines.append(f"     ✓ {assessment.pros[0]}")
        lines.append("")
    
    # Weak fits section
    weak_fits = assessments_db.get_assessments(max_fit=59)
    if weak_fits:
        lines.append("🔴 WEAK FITS (SKIP)")
        lines.append("-" * 80)
        for assessment in weak_fits:
            job = jobs.get(assessment.job_id)
            if job:
                lines.append(f"\n{assessment.fit_score}% — {job.title} @ {job.company}")
                if assessment.red_flags:
                    lines.append(f"     Issues: {'; '.join(assessment.red_flags[:2])}")
        lines.append("")
    
    lines.append("=" * 80)
    return "\n".join(lines)


def generate_json_report(
    jobs_db: JobDatabase,
    assessments_db: AssessmentDatabase,
) -> dict[str, Any]:
    """Generate a JSON format report."""
    
    jobs = {job.job_id: job for job in jobs_db.get_jobs()}
    assessments = assessments_db.get_assessments()
    summary = assessments_db.get_summary()
    
    # Build detailed assessments with job info
    detailed = []
    for assessment in assessments:
        job = jobs.get(assessment.job_id)
        if job:
            detailed.append({
                "fit_score": assessment.fit_score,
                "recommendation": assessment.recommendation,
                "job": {
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "url": job.url,
                },
                "assessment": assessment.to_dict(),
            })
    
    return {
        "summary": summary,
        "assessments": sorted(detailed, key=lambda x: x["fit_score"], reverse=True),
    }


def generate_html_report(
    jobs_db: JobDatabase,
    assessments_db: AssessmentDatabase,
) -> str:
    """Generate an HTML format report."""
    
    data = generate_json_report(jobs_db, assessments_db)
    summary = data["summary"]
    assessments = data["assessments"]
    
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html>")
    html.append("<head>")
    html.append("<meta charset='UTF-8'>")
    html.append("<title>Job Assessment Report</title>")
    html.append("<style>")
    html.append("""
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #2563eb; padding-bottom: 10px; }
        h2 { color: #2563eb; margin-top: 30px; }
        .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
        .stat { background: #f0f9ff; padding: 15px; border-radius: 6px; text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #2563eb; }
        .stat-label { font-size: 12px; color: #666; margin-top: 5px; }
        .job-card { border: 1px solid #ddd; padding: 20px; margin: 15px 0; border-radius: 6px; }
        .strong { border-left: 4px solid #10b981; }
        .good { border-left: 4px solid #f59e0b; }
        .weak { border-left: 4px solid #ef4444; }
        .job-title { font-size: 18px; font-weight: bold; color: #333; }
        .job-company { color: #666; margin: 5px 0; }
        .job-meta { font-size: 14px; color: #999; margin-top: 10px; }
        .score { font-size: 28px; font-weight: bold; }
        .recommendation { margin: 10px 0; }
        .badge { display: inline-block; padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-green { background: #d1fae5; color: #065f46; }
        .badge-yellow { background: #fef3c7; color: #78350f; }
        .badge-red { background: #fee2e2; color: #7f1d1d; }
        .skills { margin: 10px 0; }
        .skill { display: inline-block; background: #e0e7ff; color: #3730a3; padding: 4px 8px; border-radius: 3px; margin: 3px; font-size: 12px; }
        .red-flag { color: #dc2626; margin: 5px 0; }
        footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }
    """)
    html.append("</style>")
    html.append("</head>")
    html.append("<body>")
    html.append("<div class='container'>")
    
    html.append("<h1>📊 Job Assessment Report</h1>")
    
    # Summary stats
    html.append("<div class='summary'>")
    html.append(f"<div class='stat'><div class='stat-value'>{summary['total_assessed']}</div><div class='stat-label'>Total Assessed</div></div>")
    html.append(f"<div class='stat'><div class='stat-value'>{summary['average_fit_score']:.0f}</div><div class='stat-label'>Avg Fit Score</div></div>")
    html.append(f"<div class='stat'><div class='stat-value'>{summary['strong_fits_80_plus']}</div><div class='stat-label'>Strong Fits</div></div>")
    html.append(f"<div class='stat'><div class='stat-value'>{summary['good_fits_60_79']}</div><div class='stat-label'>Good Fits</div></div>")
    html.append("</div>")
    
    # Job cards
    for item in assessments:
        assessment = item["assessment"]
        job = item["job"]
        score = item["fit_score"]
        
        if score >= 80:
            css_class = "strong"
            badge_class = "badge-green"
        elif score >= 60:
            css_class = "good"
            badge_class = "badge-yellow"
        else:
            css_class = "weak"
            badge_class = "badge-red"
        
        html.append(f"<div class='job-card {css_class}'>")
        html.append(f"<div style='display: flex; justify-content: space-between; align-items: start;'>")
        html.append(f"<div><div class='job-title'>{job['title']}</div>")
        html.append(f"<div class='job-company'>{job['company']}</div>")
        html.append(f"<div class='job-meta'>{job['location']}")
        if job['salary_min'] and job['salary_max']:
            html.append(f" • ${job['salary_min']:,} - ${job['salary_max']:,}")
        html.append(f"</div></div>")
        html.append(f"<div style='text-align: right;'>")
        html.append(f"<div class='score'>{score}%</div>")
        html.append(f"<span class='badge {badge_class}'>{assessment['recommendation'].split('—')[0].strip()}</span>")
        html.append(f"</div></div>")
        
        if assessment['key_skills_match']:
            html.append("<div class='skills'>")
            for skill in assessment['key_skills_match'][:3]:
                html.append(f"<span class='skill'>{skill}</span>")
            html.append("</div>")
        
        if assessment['red_flags']:
            html.append("<div class='red-flag'>")
            for flag in assessment['red_flags'][:2]:
                html.append(f"⚠️ {flag}<br>")
            html.append("</div>")
        
        html.append("</div>")
    
    html.append("<footer>Generated by job-search-agent Phase 2: Job Assessment</footer>")
    html.append("</div></body></html>")
    
    return "\n".join(html)


def main():
    parser = argparse.ArgumentParser(description="Generate job assessment reports")
    parser.add_argument(
        "--assessments",
        default="data/assessments.json",
        help="Assessments JSON file"
    )
    parser.add_argument(
        "--jobs",
        default="data/jobs.json",
        help="Jobs JSON file"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Report format (default: text)"
    )
    parser.add_argument(
        "--output",
        help="Output file (if not specified, prints to stdout)"
    )
    
    args = parser.parse_args()
    
    # Load data
    jobs_db = JobDatabase(Path(args.jobs))
    assessments_db = AssessmentDatabase(Path(args.assessments))
    
    # Generate report
    if args.format == "text":
        report = generate_text_report(jobs_db, assessments_db)
    elif args.format == "json":
        report = json.dumps(generate_json_report(jobs_db, assessments_db), indent=2)
    elif args.format == "html":
        report = generate_html_report(jobs_db, assessments_db)
    
    # Output
    if args.output:
        Path(args.output).write_text(report)
        print(f"✅ Report saved to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
