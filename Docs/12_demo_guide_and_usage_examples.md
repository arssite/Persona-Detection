# Demo Guide & Usage Examples

This guide shows how to use each input mode with step-by-step examples and expected outputs.

---

## Input Mode 1: Email Only (Current, Highest Confidence)

### When to use:
- You have the person's corporate email
- Most common recruiting scenario

### Steps:
1. Navigate to the app (`http://localhost:5173` in dev)
2. Select **📧 Email** tab (default)
3. Enter: `firstname.lastname@company.com`
4. Click **Analyze**

### Example:
**Input:**
```
Email: satya.nadella@microsoft.com
```

**What happens:**
1. Backend parses email:
   - Domain: `microsoft.com`
   - Name guess: `Satya Nadella`
2. Scrapes:
   - Microsoft company website (`/about`, `/careers`, etc.)
   - DuckDuckGo searches: company info, person mentions, news, hiring signals
   - GitHub hint search (optional)
3. LLM synthesis with evidence
4. Returns: `AnalyzeResponse` with confidence + recommendations + evidence

**Expected Output:**
- Confidence: **HIGH** (email = authoritative source)
- Company profile: Microsoft products, recent news, hiring
- Study of person: likely role (CEO), communication style (formal, strategic)
- Recommendations: tone (professional), connecting points (cloud/AI transformation)
- Evidence: 15–25 items from microsoft.com + DuckDuckGo

**Time:** ~15–30 seconds (depends on scraping + LLM)

---

## Input Mode 2: Email + Optional Enrichment (Path A)

### When to use:
- You have email AND know their LinkedIn/GitHub
- Want richer technical/professional context

### Steps:
1. Select **📧 Email** tab
2. Enter email
3. Expand **"+ Optional: Add LinkedIn or GitHub for richer insights"**
4. Enter LinkedIn URL and/or GitHub username
5. Click **Analyze**

### Example 1: Email + LinkedIn
**Input:**
```
Email: sam.altman@openai.com
LinkedIn: https://linkedin.com/in/sam-altman
```

**What happens:**
1. Email pipeline (as above)
2. **LinkedIn enrichment**:
   - DuckDuckGo search: `site:linkedin.com/in/sam-altman`
   - Extract public snippet: headline, current role, company
   - Add to evidence (weight 0.9)
3. Merge evidence before LLM
4. Cross-validation: email domain (`openai.com`) vs LinkedIn company (`OpenAI`) → match → confidence boost

**Expected Output:**
- Confidence: **HIGH** (email + LinkedIn cross-validated)
- Study of person: role validated ("CEO at OpenAI" from LinkedIn headline)
- Evidence: email sources + 1–2 LinkedIn snippet items

### Example 2: Email + GitHub
**Input:**
```
Email: guido@python.org
GitHub: gvanrossum
```

**What happens:**
1. Email pipeline
2. **GitHub enrichment**:
   - GitHub API: `/users/gvanrossum`, `/users/gvanrossum/repos`
   - Extract: bio, company, top languages, recent repos
   - Add to evidence (weight 0.85)
3. LLM synthesis includes technical context (languages, projects)

**Expected Output:**
- Confidence: **HIGH**
- Study of person: includes technical depth ("Creator of Python, primarily uses Python/C")
- Evidence: email sources + GitHub profile item

### Example 3: Email + LinkedIn + GitHub (Richest)
**Input:**
```
Email: alex@company.com
LinkedIn: https://linkedin.com/in/alex-smith
GitHub: alexsmith
```

**Expected Output:**
- Confidence: **HIGH** (three sources cross-validated)
- Most comprehensive persona (professional role from LinkedIn, technical skills from GitHub, company context from email domain)

---

## Input Mode 3: Name + Company (Path C, No Email Required)

### When to use:
- You DON'T have the person's email
- Common in cold outreach / research scenarios

### Steps:
1. Select **👤 Name + Company** tab
2. Enter:
   - First Name
   - Last Name
   - Company (can be company name or domain)
3. Click **Analyze**

### Example 1: Name + Company Name
**Input:**
```
First Name: Jensen
Last Name: Huang
Company: NVIDIA
```

**What happens:**
1. Backend resolves company:
   - Search DDG: `"NVIDIA" official website`
   - Extract domain from top result: `nvidia.com`
   - Confidence: medium (via search)
2. Creates synthetic email: `jensen.huang@nvidia.com`
3. Scrapes:
   - DuckDuckGo: `"Jensen Huang" "NVIDIA"`
   - DuckDuckGo: `"Jensen Huang" site:linkedin.com/in "NVIDIA"` (LinkedIn snippet)
   - nvidia.com company site
   - GitHub hint search
4. LLM synthesis

**Expected Output:**
- Confidence: **MEDIUM** (no email validation, name is somewhat common)
- Company profile: NVIDIA products, GPU/AI focus
- Study of person: likely role (CEO, inferred from search results)
- Evidence: 8–15 items (thinner than email mode, but sufficient)

**Note:** Common names (e.g., "John Smith") may have lower confidence due to disambiguation difficulty.

### Example 2: Name + Domain
**Input:**
```
First Name: Elon
Last Name: Musk
Company: tesla.com
```

**What happens:**
1. Backend detects `tesla.com` is already a domain → skip resolution
2. Confidence: **high** (domain provided directly)
3. Scrapes tesla.com + DuckDuckGo for "Elon Musk"

**Expected Output:**
- Confidence: **MEDIUM-HIGH** (direct domain + distinctive name)
- Evidence: richer than generic name+company

---

## Input Mode 4: Name + Company + Optional Enrichment (Combined)

### When to use:
- No email, but you have LinkedIn/GitHub
- Best of Path C + Path A

### Example:
**Input:**
```
First Name: Demis
Last Name: Hassabis
Company: DeepMind
LinkedIn: https://linkedin.com/in/demis-hassabis
GitHub: (none)
```

**What happens:**
1. Resolve `DeepMind` → `deepmind.com` (or `deepmind.google` if Google subsidiary detected)
2. LinkedIn snippet enrichment
3. Cross-validate: company from LinkedIn headline vs resolved domain
4. Merge evidence

**Expected Output:**
- Confidence: **MEDIUM** (name+company + LinkedIn validation)
- Study of person: validated role from LinkedIn + company context
- Evidence: name+company sources + LinkedIn snippet

---

## Edge Cases & Error Handling

### Case 1: Invalid Email
**Input:**
```
Email: invalid@gmail.com
```
**Output:**
```
Error: Invalid corporate email
```
(Free domain blocked)

### Case 2: Company Not Found
**Input:**
```
Name: John Doe
Company: NonexistentCorp123
```
**What happens:**
- Domain resolution: search returns no match
- Fallback: guess domain (`nonexistentcorp123.com`)
- Crawl fails → rely on DDG search only
**Output:**
- Confidence: **LOW**
- Evidence: 2–5 items (search only)

### Case 3: Very Common Name
**Input:**
```
Name: John Smith
Company: Microsoft
```
**What happens:**
- DDG search: `"John Smith" "Microsoft"` → 1000s of results
- Backend filters by company context
- But still ambiguous
**Output:**
- Confidence: **LOW** (flagged as common name)
- Warning: "Common name—results may be ambiguous"

### Case 4: LinkedIn URL Doesn't Exist
**Input:**
```
Email: test@company.com
LinkedIn: https://linkedin.com/in/fake-profile-12345
```
**What happens:**
- LinkedIn snippet fetch: DDG search returns 0 results
- Skip LinkedIn enrichment, continue with email
**Output:**
- Confidence: same as email-only (no boost)
- Evidence: email sources only

### Case 5: GitHub Username Doesn't Exist
**Input:**
```
Email: test@company.com
GitHub: thisuserdoesnotexist12345
```
**What happens:**
- GitHub API: 404 error
- Skip GitHub enrichment, continue
**Output:**
- Same as email-only

---

## Performance Expectations

| Input Mode | Typical Time | Evidence Count | Confidence |
|------------|--------------|----------------|------------|
| Email only | 15–30s | 15–25 | HIGH |
| Email + LinkedIn | 20–35s | 16–27 | HIGH |
| Email + GitHub | 20–35s | 16–27 | HIGH |
| Email + LinkedIn + GitHub | 25–40s | 17–30 | HIGH |
| Name + Company | 20–35s | 8–15 | MEDIUM |
| Name + Company + LinkedIn | 25–40s | 10–18 | MEDIUM |

**Notes:**
- First request per domain/person is slower (no cache)
- Subsequent requests (within 5 min): instant (cache hit)
- LLM quota exhausted: returns 429 with retry-after

---

## Recruiter Talk Track (Demo Script)

### Opening (10 seconds):
> "This tool generates meeting prep coaching from public web signals. You can use it with just an email, or if you don't have an email, with a name and company."

### Demo Flow (2 minutes):

**Step 1: Show Email Mode**
> "Let me show you the most common case. I'll enter a corporate email."
- Type: `satya.nadella@microsoft.com`
- Click Analyze
- While loading: "It's scraping Microsoft's site, running searches, and using AI to synthesize."
- Show results:
  - "Here's the confidence level—HIGH because email is authoritative."
  - "One-minute brief for quick prep."
  - "Study of person—likely role, communication style."
  - "Evidence panel—every claim is backed by a source."

**Step 2: Show Name+Company Mode (Tab Switch)**
> "If I don't have an email, I can switch to Name + Company."
- Click **👤 Name + Company** tab
- Enter: `Jensen Huang`, `NVIDIA`
- Click Analyze
- "It resolves the company domain, searches for the person, and generates the same output."
- Show results:
  - "Confidence is MEDIUM—no email to validate, but still useful."

**Step 3: Show Optional Enrichment (Collapsible)**
> "And if I have their LinkedIn or GitHub, I can add it for richer insights."
- Expand optional fields
- Enter LinkedIn URL
- "This cross-validates and boosts confidence."

### Closing (10 seconds):
> "All data is public-only—no paid APIs, no scraping behind login. And it's transparent—you see exactly what sources the AI used."

---

## Screenshots Guidance (For README/Pitch Deck)

### Screenshot 1: Email Mode (Before Submit)
- Capture: Email input filled, optional section collapsed
- Annotate: "Primary input: corporate email"

### Screenshot 2: Name+Company Mode (Before Submit)
- Capture: Name+Company tab active, fields filled
- Annotate: "Alternative: works without email"

### Screenshot 3: Results View (Confidence + Brief)
- Capture: Confidence meter + one-minute brief card
- Annotate: "Confidence-labeled output"

### Screenshot 4: Evidence Panel
- Capture: Evidence list with sources + URLs
- Annotate: "Every claim is backed by sources"

### Screenshot 5: Mr Assistant Tab
- Capture: Chat interface with session
- Annotate: "Conversational follow-up for pitch tailoring"

---

## Next: Creating GIFs / Videos

If you want animated demos:
1. Use **ScreenToGif** (Windows) or **Kap** (macOS)
2. Record 15–30 second flows:
   - Email input → Analyze → Show results
   - Tab switch → Name+Company → Analyze
3. Export as GIF (< 5MB for README embedding)

Or use **Loom** / **Screen Studio** for higher-quality video (like your `Output_For_V1.mp4`).
