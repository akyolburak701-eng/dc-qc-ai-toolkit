# Data Center QC AI Toolkit

Three prototype AI tools for data center quality control, built with Streamlit and the Claude API.

## Problem
QC managers lose hours to repetitive paperwork and manual trend analysis. These tools cut that time and make recurring issues visible.

## Tools
1. **NCR Drafter** - rough field notes into a formal non-conformance report (root cause, corrective action, verification).
2. **Photo Defect Spotter** - site photo into a structured draft punch list with severity and confidence.
3. **QC Dashboard** - Pareto chart, first-pass rate, trade/area trends, and an AI-written weekly summary (synthetic data).

## Run it
```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key   # Windows: set ANTHROPIC_API_KEY=your_key
streamlit run app.py
```
Optional: `CLAUDE_MODEL` env var to switch models.

## Results (fill in after testing)
- NCR drafting time: ~__ min manual vs ~__ min with tool (n=__ test notes)
- Photo spotter: caught __ of __ planted defects in __ test images

## Notes
- Uses synthetic and public data only; no confidential employer or client material.
- AI output is a draft for human verification, not a replacement for inspection judgment.
