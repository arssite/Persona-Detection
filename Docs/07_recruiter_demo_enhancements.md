# Recruiter Demo Enhancements (Implemented)

## New public-signal sources
- **Company website**: conservative crawl + text extraction (public pages only)
- **DuckDuckGo search**:
  - company overview
  - news/funding/press
  - hiring/careers pages
  - person lookup
  - GitHub hints
- **GitHub public API**: only when a GitHub profile URL is discovered via public search results

## Safety policy
- No authenticated scraping (no LinkedIn login)
- LinkedIn appears only if it shows up as a public search snippet + link
- robots.txt respected for company-site crawling

## New output fields (API)
- `one_minute_brief`
- `questions_to_ask`
- `email_openers` (formal/warm/technical)
- `red_flags`
- `company_profile`
- `company_confidence` / `person_confidence` (optional)
- `github_profile` (optional)

## Frontend sections
- One-minute brief
- Company profile
- Study of person (expanded)
- Questions to ask
- Email openers
- Red flags
- GitHub card (if present)
- Evidence + breakdown chart
