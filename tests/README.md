# XOCOA QA & Evaluation Status

**Last Updated:** 2026-02-10

## Current Status
- **Baseline Score (Golden Set):** 94% (High confidence on core queries).
- **Stress Test Score (Silver Set):** 80% (Baseline established).
- **Known Issues:**
  - "Allergic to nuts" logic needs fixing in Channel A.
  - "How do you make chocolate" is classified as search (should be chat).
  - Typos ("mikl") fixed in Router but pending re-evaluation.

## How to Resume
1. **Start Backend:**
   ```bash
   docker-compose up -d xocoa-backend
   ```
2. **Run Evaluation:**
   ```bash
   python3 tools/evaluate_rag.py
   ```
3. **Analyze Results:** Check `rag_evaluation_report.md`.

## Next Steps
- Implement "Allergic to" filter in `channel_a/query/parse.py`.
- Improve Router for process questions ("How do you...").
- Run `evaluate_rag.py` on `tests/data/silver_dataset.json` to verify fixes (Target: >90%).
