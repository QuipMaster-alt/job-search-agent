"""
tailor_resume.py
----------------
Takes your master RenderCV YAML + a job description and produces a
tailored YAML + rendered PDF using the Claude API.

Supports single job or batch processing from Phase 2 assessments.

Usage (single job):
    python tailor_resume.py \
        --cv Luis_CV.yaml \
        --job "path/to/job_description.txt" \
        --company "Instructure" \
        --title "VP Business Intelligence" \
        [--output-dir ./tailored_resumes]

Usage (batch from assessments):
    python tailor_resume.py \
        --cv Luis_CV.yaml \
        --batch-assess data/assessments.json \
        --jobs data/jobs.json \
        --min-fit 80 \
        [--output-dir ./tailored_resumes]

Requirements:
    pip install anthropic pyyaml
    pip install "rendercv[full]"   # Python 3.12+ required for rendercv

Environment:
    ANTHROPIC_API_KEY  — your Anthropic API key (or set in .env)
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


# ─────────────────────────────────────────────
# CONFIG — your profile context sent to Claude
# ─────────────────────────────────────────────
PROFILE_CONTEXT = """
Candidate: BI and Analytics Leader
- 15+ years experience in Business Intelligence and Data Analytics
- Targeting Director / Senior Director / VP level roles
- Based in Austin, TX (open to remote or hybrid)
- Core tools: Tableau, Power BI, Snowflake, SQL, DAX
- Sweet-spot industries: tech, SaaS, education, healthcare, operations
- Target compensation: $180k–$240k
- NOT targeting: fintech, credit risk, pure data science / ML engineering
"""

TAILOR_PROMPT = """
You are a professional resume writer helping tailor a BI/Analytics leader's
resume for a specific job posting. Your job is to make targeted, honest
edits — never fabricate experience.

## Candidate Profile
{profile}

## Job Posting
Company: {company}
Title: {title}
Location: {location}

{job_description}

## Current Resume (YAML sections only)
{cv_sections_yaml}

## Instructions
Analyze the job posting and return a modified version of the YAML sections
that best positions this candidate. You may:

1. REORDER highlights within each experience entry to front-load the most
   relevant accomplishments for this role. Do not add or remove highlights.

2. REWRITE the summary section to 2-3 sentences max, directly mirroring 
   the language and priorities of this specific job posting. Use keywords 
   from the JD naturally. Make it specific to this role and company — 
   not generic BI language.

3. REORDER skills entries to lead with the tools/categories most relevant
   to the job posting.

4. DO NOT add a top_note field. Skip this entirely.

5. DO NOT change company names, dates, titles, or invent new experience.

Return ONLY valid YAML — just the `cv.sections` dictionary contents,
plus optionally a `top_note` key at the root level.
No markdown fences, no explanation, no preamble.

Example output format:
top_note: "15+ years building analytics orgs in EdTech and SaaS"
summary:
  - Tailored summary text here...
experience:
  - company: ...
    ...
skills:
  - label: ...
    ...
"""


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def load_yaml(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_yaml(data: dict, path: Path):
    with open(path, "w") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def read_text(path: Path) -> str:
    with open(path, "r") as f:
        return f.read().strip()


def slug(text: str) -> str:
    """Convert company/title to a filesystem-safe string."""
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")


def call_claude(prompt: str, model: str = "claude-sonnet-4-5") -> str:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def parse_claude_yaml(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:yaml)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    return yaml.safe_load(cleaned)


def render_pdf(yaml_path: Path, output_dir: Path) -> Optional[Path]:
    """Render PDF using RenderCV. Returns None if rendering fails."""
    import shutil
    rendercv_path = "/Users/luismartinez/job-search-agent/venv/bin/rendercv"
    result = subprocess.run(
        [
            rendercv_path, "render",
            str(yaml_path),
            "--output-folder-name", str(output_dir),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.warning(f"⚠️  RenderCV failed: {result.stderr[:200]}")
        return None

    pdfs = list(output_dir.glob("*.pdf"))
    if pdfs:
        return pdfs[0]
    return None


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def tailor(
    cv_path: Path,
    job_title: str,
    job_company: str,
    job_location: str,
    job_description: str,
    output_dir: Path,
    dry_run: bool = False,
) -> Optional[dict]:
    """Tailor a single resume for a job posting.
    
    Returns dict with paths to generated files, or None if failed.
    """
    logger.info(f"  📝 {job_title} @ {job_company} ({job_location})")

    master_cv = load_yaml(cv_path)
    cv_sections = master_cv.get("cv", {}).get("sections", {})
    cv_sections_yaml = yaml.dump(cv_sections, allow_unicode=True, sort_keys=False)

    prompt = TAILOR_PROMPT.format(
        profile=PROFILE_CONTEXT,
        company=job_company,
        title=job_title,
        location=job_location,
        job_description=job_description,
        cv_sections_yaml=cv_sections_yaml,
    )

    if dry_run:
        logger.info("     [DRY RUN] Skipping Claude API call")
        return None

    try:
        raw_response = call_claude(prompt)
        tailored_data = parse_claude_yaml(raw_response)
    except Exception as e:
        logger.error(f"     ❌ Failed to tailor: {e}")
        return None

    # Merge with master CV
    tailored_cv = deepcopy(master_cv)
    tailored_cv["cv"]["sections"] = tailored_data.get("sections") or tailored_data

    if "top_note" in tailored_data:
        tailored_cv.setdefault("cv", {})["top_note"] = tailored_data["top_note"]

    # Save files
    date_str = datetime.today().strftime("%Y%m%d")
    company_slug = slug(job_company)
    title_slug = slug(job_title)

    # Inject company/role into cv.name so rendercv output filename is unique
    original_name = tailored_cv["cv"].get("name", "Luis_Martinez_CV")
    tailored_cv["cv"]["name"] = f"{original_name}_{company_slug}_{title_slug}"

    output_dir.mkdir(parents=True, exist_ok=True)

    tailored_yaml_path = output_dir / f"CV_{company_slug}_{title_slug}_{date_str}.yaml"
    render_output_dir = output_dir / f"{company_slug}_{title_slug}_{date_str}"

    save_yaml(tailored_cv, tailored_yaml_path)
    logger.info(f"     ✅ YAML: {tailored_yaml_path.name}")

    # Try to render PDF
    pdf_path = render_pdf(tailored_yaml_path, render_output_dir)
    if pdf_path:
        logger.info(f"     ✅ PDF: {pdf_path.name}")
    else:
        logger.warning(f"     ⚠️  PDF render skipped (rendercv not available)")

    return {
        "yaml_path": str(tailored_yaml_path),
        "pdf_path": str(pdf_path) if pdf_path else None,
        "company": job_company,
        "title": job_title,
    }

def tailor_batch(
    cv_path: Path,
    jobs_file: Path,
    assessments_file: Path,
    min_fit: int = 80,
    output_dir: Path = Path("tailored_resumes"),
    dry_run: bool = False,
) -> list[dict]:
    """Tailor resumes for all jobs above a fit threshold.
    
    Returns list of results from tailor().
    """
    logger.info(f"\n🎯 Batch tailoring resumes for jobs with fit ≥ {min_fit}")

    # Load data
    jobs_data = json.loads(jobs_file.read_text())
    assessments_data = json.loads(assessments_file.read_text())

    # Filter to strong fits
    strong_jobs = []
    for job_id, job_data in jobs_data.items():
        if job_id in assessments_data:
            assessment = assessments_data[job_id]
            if assessment["fit_score"] >= min_fit:
                strong_jobs.append((job_data, assessment))

    strong_jobs.sort(key=lambda x: x[1]["fit_score"], reverse=True)

    logger.info(f"  Found {len(strong_jobs)} jobs with fit ≥ {min_fit}")

    results = []
    for job_data, assessment in strong_jobs:
        result = tailor(
            cv_path=cv_path,
            job_title=job_data["title"],
            job_company=job_data["company"],
            job_location=job_data["location"],
            job_description=f"URL: {job_data['url']}\n\n{job_data.get('description', '')}",
            output_dir=output_dir,
            dry_run=dry_run,
        )
        if result:
            results.append(result)

    logger.info(f"\n✅ Tailored {len(results)} resumes")
    return results


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Tailor RenderCV resume for job postings (single or batch)."
    )
    
    # Single job mode
    parser.add_argument("--cv", required=True, help="Path to master RenderCV YAML file")
    parser.add_argument("--job", help="Path to job description text file (single mode)")
    parser.add_argument("--company", help="Company name (single mode)")
    parser.add_argument("--title", help="Job title (single mode)")
    
    # Batch mode
    parser.add_argument("--batch-assess", help="Path to assessments JSON (batch mode)")
    parser.add_argument("--jobs", help="Path to jobs JSON (batch mode)")
    parser.add_argument("--min-fit", type=int, default=80, help="Min fit score for batch (default: 80)")
    
    # Common
    parser.add_argument("--output-dir", default="tailored_resumes", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Don't call Claude API")
    
    args = parser.parse_args()

    cv_path = Path(args.cv)
    if not cv_path.exists():
        logger.error(f"❌ CV file not found: {cv_path}")
        sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY") and not args.dry_run:
        logger.error("❌ ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    output_dir = Path(args.output_dir)

    # Batch mode
    if args.batch_assess and args.jobs:
        assessments_path = Path(args.batch_assess)
        jobs_path = Path(args.jobs)
        if not assessments_path.exists() or not jobs_path.exists():
            logger.error(f"❌ Batch files not found")
            sys.exit(1)
        
        tailor_batch(
            cv_path=cv_path,
            jobs_file=jobs_path,
            assessments_file=assessments_path,
            min_fit=args.min_fit,
            output_dir=output_dir,
            dry_run=args.dry_run,
        )
    # Single mode
    elif args.job and args.company and args.title:
        job_path = Path(args.job)
        if not job_path.exists():
            logger.error(f"❌ Job description file not found: {job_path}")
            sys.exit(1)
        
        job_description = read_text(job_path)
        
        logger.info(f"\n📄 Tailoring resume for {args.title} @ {args.company}")
        tailor(
            cv_path=cv_path,
            job_title=args.title,
            job_company=args.company,
            job_location="",
            job_description=job_description,
            output_dir=output_dir,
            dry_run=args.dry_run,
        )
        logger.info(f"\n📁 Outputs in: {output_dir}")
    else:
        logger.error("❌ Specify either:\n  Single: --job, --company, --title\n  Batch: --batch-assess, --jobs")
        sys.exit(1)


if __name__ == "__main__":
    main()
