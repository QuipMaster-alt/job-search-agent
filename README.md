# job-search-agent

AI-powered job search agent that finds job postings, assesses fit and pay, and tailors your resume for ATS compatibility.

## Features

✨ **Job Discovery** — Search across Indeed, LinkedIn, Glassdoor, and other job boards
🤖 **Smart Assessment** — Claude analyzes job fit, salary alignment, and red flags
📄 **Resume Tailoring** — Automatically adapt your resume for each role and optimize for ATS
📊 **Tracking** — Store and organize all discovered jobs locally

## Quick Start

### Installation

```bash
# Clone the repo
git clone https://github.com/QuipMaster-alt/job-search-agent.git
cd job-search-agent

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

```bash
# Create .env file with your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Or export as environment variable
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Usage

#### Phase 1: Discover Jobs

Search for jobs across multiple job boards:

```bash
python job_scraper.py \
  --keyword "Business Intelligence" \
  --location "Austin, TX" \
  --sources indeed,linkedin,glassdoor \
  --limit 50
```

Output: Jobs saved to `data/jobs.json`

#### Phase 2: Assess Job Fit

Analyze each job posting for fit, salary, and red flags using Claude AI:

```bash
# With API key (uses real Claude)
export ANTHROPIC_API_KEY="sk-ant-..."
python job_assessor.py --jobs data/jobs.json --limit 5

# Without API (demo mode with mock data)
python demo_assessor.py

# Generate reports
python report_assessments.py --format text
python report_assessments.py --format html --output report.html
python report_assessments.py --format json
```

Output: Assessments saved to `data/assessments.json`

**Fit Score Guide:**
- 🟢 **80+** — Strong fit, apply immediately
- 🟡 **60-79** — Good opportunity, consider applying
- 🔴 **Below 60** — Weak fit, likely mismatch

#### Phase 3: Tailor Resume

Adapt your resume for a specific job:

```bash
python tailor_resume.py \
  --cv Luis_CV.yaml \
  --job "path/to/job_description.txt" \
  --company "Instructure" \
  --title "VP Business Intelligence"
```

## Project Structure

```
job-search-agent/
├── job_scraper.py         # Phase 1: Job discovery across multiple sources
├── job_assessor.py        # Phase 2: Claude-powered fit/salary analysis (coming)
├── tailor_resume.py       # Phase 3: Resume tailoring for ATS
├── main.py                # CLI orchestrator (coming)
├── data/
│   └── jobs.json          # Job database
├── tailored_resumes/      # Output directory
├── requirements.txt
└── README.md
```

## Configuration

Edit your profile context in `tailor_resume.py`:

```python
PROFILE_CONTEXT = """
Candidate: BI and Analytics Leader
- 15+ years experience in Business Intelligence and Data Analytics
- Targeting Director / Senior Director / VP level roles
- Based in Austin, TX (open to remote or hybrid)
- Core tools: Tableau, Power BI, Snowflake, SQL, DAX
- Sweet-spot industries: tech, SaaS, education, healthcare, operations
- Target compensation: $180k–$240k
"""
```

## Development Phases

- ✅ **Phase 1**: Job Discovery (Indeed, LinkedIn, Glassdoor)
- 🔄 **Phase 2**: Job Assessment (fit score, salary validation, red flags)
- 📝 **Phase 3**: Resume Tailoring & PDF generation
- 🚀 **Phase 4**: Integration & CLI orchestrator

## Testing

```bash
# Test the scraper module
python test_scraper.py
```

## Requirements

- Python 3.12+ (required for RenderCV)
- Anthropic API key (for Claude)
- Internet connection (for job board scraping)

## License

MIT
