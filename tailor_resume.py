"""
tailor_resume.py
----------------
Takes your master RenderCV YAML + a job description and produces a
tailored YAML + rendered PDF using the Claude API.

Usage:
    python tailor_resume.py \
        --cv Luis_CV.yaml \
        --job "path/to/job_description.txt" \
        --company "Instructure" \
        --title "VP Business Intelligence" \
        [--output-dir ./tailored_resumes]

Requirements:
    pip install anthropic pyyaml
    pip install "rendercv[full]"   # Python 3.12+ required for rendercv

Environment:
    ANTHROPIC_API_KEY  — your Anthropic API key (or set in .env)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import anthropic
import yaml


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

{job_description}

## Current Resume (YAML sections only)
{cv_sections_yaml}

## Instructions
Analyze the job posting and return a modified version of the YAML sections
that best positions this candidate. You may:

1. REORDER highlights within each experience entry to front-load the most
   relevant accomplishments for this role. Do not add or remove highlights.

2. REWRITE the summary/objective section (if present) to directly address
   the role's key themes (e.g. EdTech transformation, SaaS scale, etc.)
   Keep it to 2–3 sentences maximum.

3. REORDER skills entries to lead with the tools/categories most relevant
   to the job posting.

4. ADD a `top_note` field at the top level (outside cv) if the job has a
   specific theme worth calling out — a one-line positioning statement.
   Keep it under 120 characters. If not needed, omit it.

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


def call_claude(prompt: str, model: str = "claude-sonnet-4-20250514") -> str:
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


def render_pdf(yaml_path: Path, output_dir: Path) -> Path:
    result = subprocess.run(
        [
            sys.executable, "-m", "rendercv", "render",
            str(yaml_path),
            "--output-folder-name", str(output_dir),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("⚠️  RenderCV stderr:\n", result.stderr)
        raise RuntimeError(f"rendercv render failed:\n{result.stdout}\n{result.stderr}")

    pdfs = list(output_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF found in {output_dir} after rendering.")
    return pdfs[0]


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def tailor(
    cv_path: Path,
    job_path: Path,
    company: str,
    title: str,
    output_dir: Path,
    dry_run: bool = False,
):
    print(f"\n🔍  Loading CV from {cv_path}")
    master_cv = load_yaml(cv_path)

    print(f"📄  Loading job description from {job_path}")
    job_description = read_text(job_path)

    cv_sections = master_cv.get("cv", {}).get("sections", {})
    cv_sections_yaml = yaml.dump(cv_sections, allow_unicode=True, sort_keys=False)

    prompt = TAILOR_PROMPT.format(
        profile=PROFILE_CONTEXT,
        company=company,
        title=title,
        job_description=job_description,
        cv_sections_yaml=cv_sections_yaml,
    )

    print(f"🤖  Calling Claude to tailor resume for {title} @ {company}...")
    if dry_run:
        print("\n[DRY RUN] Prompt preview (first 800 chars):\n")
        print(prompt[:800])
        print("\n[DRY RUN] Skipping API call and render.")
        return

    raw_response = call_claude(prompt)

    try:
        tailored_data = parse_claude_yaml(raw_response)
    except yaml.YAMLError as e:
        print("❌  Claude returned invalid YAML. Raw response saved to debug_response.txt")
        Path("debug_response.txt").write_text(raw_response)
        raise e

    tailored_cv = deepcopy(master_cv)
    tailored_cv["cv"]["sections"] = tailored_data.get("sections") or tailored_data

    if "top_note" in tailored_data:
        tailored_cv.setdefault("cv", {})["top_note"] = tailored_data["top_note"]

    date_str = datetime.today().strftime("%Y%m%d")
    company_slug = slug(company)
    title_slug = slug(title)
    output_dir.mkdir(parents=True, exist_ok=True)

    tailored_yaml_path = output_dir / f"Luis_CV_{company_slug}_{title_slug}_{date_str}.yaml"
    render_output_dir = output_dir / f"{company_slug}_{date_str}"

    save_yaml(tailored_cv, tailored_yaml_path)
    print(f"✅  Tailored YAML saved: {tailored_yaml_path}")

    print(f"🖨️   Rendering PDF with RenderCV...")
    try:
        pdf_path = render_pdf(tailored_yaml_path, render_output_dir)
        print(f"✅  PDF ready: {pdf_path}")
    except Exception as e:
        print(f"⚠️   PDF render failed (YAML was saved): {e}")
        print(f"     You can render manually: rendercv render \"{tailored_yaml_path}\"")

    print(f"\n📁  All outputs in: {output_dir}")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Tailor a RenderCV resume YAML for a specific job posting using Claude."
    )
    parser.add_argument("--cv", required=True, help="Path to your master RenderCV YAML file")
    parser.add_argument("--job", required=True, help="Path to job description text file")
    parser.add_argument("--company", required=True, help='Company name, e.g. "Instructure"')
    parser.add_argument("--title", required=True, help='Job title, e.g. "VP Business Intelligence"')
    parser.add_argument("--output-dir", default="./tailored_resumes")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cv_path = Path(args.cv)
    job_path = Path(args.job)
    if not cv_path.exists():
        print(f"❌  CV file not found: {cv_path}")
        sys.exit(1)
    if not job_path.exists():
        print(f"❌  Job description file not found: {job_path}")
        sys.exit(1)
    if not os.environ.get("ANTHROPIC_API_KEY") and not args.dry_run:
        print("❌  ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    tailor(
        cv_path=cv_path,
        job_path=job_path,
        company=args.company,
        title=args.title,
        output_dir=Path(args.output_dir),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
