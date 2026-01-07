# Meeting Intelligence MVP (Overview)

## Goal
Turn a corporate email into AI-inferred meeting intelligence using **public web signals**.

## Constraints
- Corporate emails only
- Public web only (no paid enrichment APIs)
- LinkedIn via search-result preview snippets only (no login, no scraping authenticated pages)
- Outputs must be probabilistic and confidence-labeled

## High-Level Flow
1. User enters corporate email
2. Backend validates and extracts name/domain (best effort)
3. Live web research (search + company site)
4. Signal fusion + confidence scoring
5. LLM generates strict JSON persona + meeting coaching
6. Frontend renders output + confidence + evidence
