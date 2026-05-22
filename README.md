# job-search-agent

AI-powered job search agent that finds job postings, assesses fit and pay, and tailors your resume for ATS compatibility.

## 🚀 Quick Start

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

### Complete Workflow (One Command!)

```bash
# Demo mode (no API key needed)
python main.py \
  --keyword "Business Intelligence" \
  --location "Austin, TX" \
  --demo

# Real search + assessment + tailoring
export ANTHROPIC_API_KEY="sk-ant-..."
python main.py \
  --keyword "Business Intelligence" \
  --location "Austin, TX" \
  --cv Luis_CV.yaml \
  --tailor-resumes
```

**Output:** Jobs, assessments, tailored resumes, and reports in `search_results/`

## Features

✨ **Job Discovery** — Search across Indeed, LinkedIn, Glassdoor
🤖 **Smart Assessment** — Claude analyzes job fit, salary alignment, red flags
📄 **Resume Tailoring** — Adapt resume for each role, optimize for ATS
📊 **Comprehensive Reports** — Text, HTML, and JSON formats
🔀 **Batch Processing** — Process multiple jobs automatically

## 4-Phase Workflow

### Phase 1: Job Discovery

```bash
python job_scraper.py \
  --keyword "Business Intelligence" \
  --location "Austin, TX" \
  --sources indeed,linkedin,glassdoor \
  --limit 50
```

### Phase 2: Job Assessment

```bash
# Real assessment (requires API key)
export ANTHROPIC_API_KEY="sk-ant-..."
python job_assessor.py

# Demo assessment (no API needed)
python demo_assessor.py

# Generate reports
python report_assessments.py --format text
python report_assessments.py --format html --output report.html
```

**Fit Scores:**
- 🟢 80+ — Strong fit
- 🟡 60-79 — Good fit
- 🔴 <60 — Weak fit

### Phase 3: Resume Tailoring

**Single job:**
```bash
python tailor_resume.py \
  --cv Luis_CV.yaml \
  --job job_description.txt \
  --company "Instructure" \
  --title "VP Business Intelligence"
```

**Batch mode:**
```bash
python tailor_resume.py \
  --cv Luis_CV.yaml \
  --batch-assess data/assessments.json \
  --jobs data/jobs.json \
  --min-fit 80
```

### Phase 4: Orchestration

Run all phases in one command:

```bash
python main.py \
  --keyword "Business Intelligence" \
  --location "Austin, TX" \
  --cv Luis_CV.yaml \
  --tailor-resumes
```

**Options:**
- `--no-discover` — Skip job discovery
- `--no-assess` — Skip assessment
- `--tailor-resumes` — Tailor resumes
- `--no-report` — Skip reports
- `--demo` — Use mock data
- `--min-fit 75` — Custom fit threshold
- `--limit 100` — Custom job limit

## Project Structure

```
job-search-agent/
├── main.py                 # ⭐ Unified orchestrator (Phase 4)
├── job_scraper.py         # Phase 1: Job discovery
├── job_assessor.py        # Phase 2: Job assessment
├── tailor_resume.py       # Phase 3: Resume tailoring
├── report_assessments.py  # Report generation
├── demo_*.py              # Demo scripts
├── test_*.py              # Unit tests
├── data/
│   ├── jobs.json
│   └── assessments.json
└── search_results/        # Output directory
```

## Configuration

Update your profile in `job_assessor.py`:

```python
PROFILE_CONTEXT = """
Candidate: BI and Analytics Leader
- 15+ years in Business Intelligence and Data Analytics
- Director / Senior Director / VP level
- Austin, TX (remote/hybrid open)
- Tools: Tableau, Power BI, Snowflake, SQL, DAX
- Industries: Tech, SaaS, Education, Healthcare
- Target: $180k–$240k
"""
```

## Testing

```bash
python test_scraper.py
python test_assessor.py
python demo_assessor.py
python demo_tailor.py
```

## Requirements

- Python 3.12+ (for RenderCV)
- Anthropic API key (optional for demo mode)
- Internet connection

## Pricing

- Job Discovery: Free (scraping)
- Assessment: $0.01-0.05 per job (Claude API)
- Resume Tailoring: $0.05-0.15 per resume (Claude API)
- Example: 50 jobs + 5 resumes ≈ $0.50-$3.00

## Development Status

✅ Phase 1: Job Discovery
✅ Phase 2: Job Assessment
✅ Phase 3: Resume Tailoring
✅ Phase 4: Orchestration

## License

MIT
