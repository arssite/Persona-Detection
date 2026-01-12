import { useMemo, useState } from "react";
import "./App.css";
import { analyze, type AnalyzeResponse } from "./api/client";
import { MrAssistant } from "./components/MrAssistant";
import { ConfidenceBadge } from "./components/ConfidenceBadge";
import { ConfidenceMeter } from "./components/ConfidenceMeter";
import { EvidenceBreakdownChart } from "./components/EvidenceBreakdownChart";
import { JsonDetails } from "./components/JsonDetails";
import { BubbleLoader } from "./components/BubbleLoader";
import { UseCasesRotator } from "./components/UseCasesRotator";
import { Card } from "./components/Card";
import { GitHubCard } from "./components/GitHubCard";
import InstagramCard from "./components/InstagramCard";
import MediumCard from "./components/MediumCard";
import XCard from "./components/XCard";

function App() {
  const [inputMode, setInputMode] = useState<"email" | "name_company" | "name_email">("email");
  
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [company, setCompany] = useState("");
  
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [githubUsername, setGithubUsername] = useState("");

  // Social discovery/selection
  const [allowDiscovery, setAllowDiscovery] = useState(true);
  const [selectedInstagram, setSelectedInstagram] = useState<string>("");
  const [selectedX, setSelectedX] = useState<string>("");
  const [selectedMedium, setSelectedMedium] = useState<string>("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalyzeResponse | null>(null);

  const canSubmit = useMemo(() => {
    if (inputMode === "email") {
      return email.trim().length > 5 && email.includes("@");
    }
    if (inputMode === "name_email") {
      return (
        firstName.trim().length >= 2 &&
        lastName.trim().length >= 2 &&
        email.trim().length > 5 &&
        email.includes("@")
      );
    }
    // name_company
    return firstName.trim().length >= 2 && lastName.trim().length >= 2 && company.trim().length >= 2;
  }, [inputMode, email, firstName, lastName, company]);

  const [stage, setStage] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setData(null);
    setLoading(true);
    setStage("Collecting public signals…");

    try {
      // Small fake progress to make demo feel alive (backend is non-streaming).
      const t1 = window.setTimeout(() => setStage("Searching the web…"), 700);
      const t2 = window.setTimeout(() => setStage("Scraping company website…"), 1400);
      const t3 = window.setTimeout(() => setStage("Generating meeting intelligence…"), 2100);

      const res = await analyze({
        email: inputMode === "email" || inputMode === "name_email" ? email.trim() : null,
        name:
          inputMode === "name_company" || inputMode === "name_email"
            ? { first: firstName.trim(), last: lastName.trim() }
            : null,
        company: inputMode === "name_company" ? company.trim() : null,
        linkedin_url: linkedinUrl.trim() || null,
        github_username: githubUsername.trim() || null,

        allow_discovery: allowDiscovery,
        instagram_url: selectedInstagram.trim() || null,
        x_url: selectedX.trim() || null,
        medium_url: selectedMedium.trim() || null,
      });
      window.clearTimeout(t1);
      window.clearTimeout(t2);
      window.clearTimeout(t3);
      setStage(null);
      setData(res);
      setActiveTab("analysis");
    } catch (err) {
      setStage(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const [activeTab, setActiveTab] = useState<"analysis" | "assistant">("analysis");

  return (
    <div className="appShell">
      <div className="appContent">
        <h1 className="pageTitle">Meeting Intelligence MVP</h1>
        <p className="subtitle">
          Enter a corporate email. We infer meeting guidance using public web signals and a lightweight RAG-style agent.
        </p>

      <div style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button
            type="button"
            className={inputMode === "email" ? "tab tabActive" : "tab"}
            onClick={() => setInputMode("email")}
          >
            📧 Email
          </button>
          <button
            type="button"
            className={inputMode === "name_company" ? "tab tabActive" : "tab"}
            onClick={() => setInputMode("name_company")}
          >
            👤 Name + Company
          </button>
          <button
            type="button"
            className={inputMode === "name_email" ? "tab tabActive" : "tab"}
            onClick={() => setInputMode("name_email")}
          >
            👤 Name + Email
          </button>
        </div>
      </div>

      <form onSubmit={onSubmit} className="topBar">
        {inputMode === "email" ? (
          <input
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="firstname.lastname@company.com"
            required
          />
        ) : inputMode === "name_email" ? (
          <div style={{ display: "grid", gap: 8 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <input
                className="input"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="First Name"
                required
              />
              <input
                className="input"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Last Name"
                required
              />
            </div>
            <input
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="firstname.lastname@company.com"
              required
            />
          </div>
        ) : (
          <div style={{ display: "grid", gap: 8 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <input
                className="input"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="First Name"
                required
              />
              <input
                className="input"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Last Name"
                required
              />
            </div>
            <input
              className="input"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Company (e.g., OpenAI or openai.com)"
              required
            />
          </div>
        )}
        
        <details style={{ marginTop: 10 }}>
          <summary style={{ cursor: "pointer", fontSize: 13, opacity: 0.8 }}>
            + Optional: Add LinkedIn, GitHub, or social profiles
          </summary>
          <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
            <input
              type="url"
              className="input"
              placeholder="LinkedIn URL (e.g., https://linkedin.com/in/username)"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
            />
            <input
              type="text"
              className="input"
              placeholder="GitHub username (e.g., torvalds)"
              value={githubUsername}
              onChange={(e) => setGithubUsername(e.target.value)}
            />

            <label style={{ display: "flex", gap: 10, alignItems: "center", fontSize: 13, opacity: 0.9 }}>
              <input
                type="checkbox"
                checked={allowDiscovery}
                onChange={(e) => setAllowDiscovery(e.target.checked)}
              />
              Auto-discover public social profiles (via search snippets)
            </label>

            <input
              type="url"
              className="input"
              placeholder="Instagram profile URL (optional)"
              value={selectedInstagram}
              onChange={(e) => setSelectedInstagram(e.target.value)}
            />
            <input
              type="url"
              className="input"
              placeholder="X/Twitter profile URL (optional)"
              value={selectedX}
              onChange={(e) => setSelectedX(e.target.value)}
            />
            <input
              type="url"
              className="input"
              placeholder="Medium profile URL (optional)"
              value={selectedMedium}
              onChange={(e) => setSelectedMedium(e.target.value)}
            />
          </div>
        </details>
        
        <button disabled={!canSubmit || loading} type="submit" className="button" style={{ marginTop: 10 }}>
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      <div className="note">Note: This tool uses public information and produces AI-inferred suggestions, not facts.</div>

      {loading && stage ? (
        <>
          <div className="status" style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <span className="pill">Status</span>
            <span>{stage}</span>
            <BubbleLoader />
          </div>
          <UseCasesRotator />
        </>
      ) : null}

      {error ? <pre className="error">{error}</pre> : null}

      <div style={{ marginTop: 18 }} className="smallTextOnDark">
        Developer: <strong style={{ color: "rgb(125, 249, 255)" }}>ANMOL R. SRIVASTAVA</strong>
      </div>

      {data ? (
        <>
          <div className="tabs">
            <button
              type="button"
              className={activeTab === "analysis" ? "tab tabActive" : "tab"}
              onClick={() => setActiveTab("analysis")}
            >
              Analysis
            </button>
            <button
              type="button"
              className={activeTab === "assistant" ? "tab tabActive" : "tab"}
              onClick={() => setActiveTab("assistant")}
            >
              Mr Assistant
            </button>
          </div>

          {activeTab === "analysis" ? <div className="grid">
          <div className="twoCol">
            <section className="card">
              <div className="cardTitle">Input</div>
              <div className="kvLabel">Email</div>
              <div className="kvValue">{data.input_email}</div>

              <div style={{ height: 10 }} />

              <div className="kvLabel">Name guess</div>
              <div>{data.person_name_guess ?? "—"}</div>

              <div style={{ height: 8 }} />

              <div className="kvLabel">Company domain</div>
              <div>{data.company_domain ?? "—"}</div>
            </section>

            <section className="card">
              <div className="cardTitle">Confidence</div>
              <ConfidenceBadge confidence={data.confidence} />
              <div style={{ marginTop: 10 }}>
                <ConfidenceMeter confidence={data.confidence} />
              </div>
            </section>
          </div>

          <Card title="One-minute brief">
            <div>{data.one_minute_brief ?? "unknown"}</div>
          </Card>

          {(data.social_selected?.length ?? 0) > 0 || (data.social_candidates?.length ?? 0) > 0 ? (
            <section className="card">
              <div className="cardTitle">Social Profiles</div>

              {(data.social_selected?.length ?? 0) > 0 ? (
                <>
                  <div className="kvLabel">Selected (user-provided / confirmed)</div>
                  <ul className="list">
                    {(data.social_selected ?? []).map((s) => (
                      <li key={`sel-${s.platform}-${s.url}`} style={{ marginBottom: 8 }}>
                        <strong style={{ textTransform: "capitalize" }}>{s.platform}:</strong>{" "}
                        <a href={s.url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                          {s.url}
                        </a>
                        {s.snippet ? <div style={{ marginTop: 4 }}>{s.snippet}</div> : null}
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <div className="smallText">No social profiles selected yet.</div>
              )}

              {(data.social_candidates?.length ?? 0) > 0 ? (
                <>
                  <div style={{ height: 10 }} />
                  <div className="kvLabel">Discovered candidates (snippets)</div>
                  {(["instagram", "x", "medium"] as const).map((platform) => {
                    const candidates = (data.social_candidates ?? []).filter((c) => c.platform === platform);
                    if (candidates.length === 0) return null;
                    return (
                      <div key={`sum-${platform}`} style={{ marginTop: 10 }}>
                        <div className="smallText" style={{ fontWeight: 700, textTransform: "capitalize" }}>
                          {platform}
                        </div>
                        <ul className="list">
                          {candidates.slice(0, 3).map((c) => (
                            <li key={`cand-${c.url}`} style={{ marginBottom: 8 }}>
                              <div style={{ fontSize: 12, opacity: 0.8 }}>
                                confidence: {(c.confidence ?? 0).toFixed(2)}
                              </div>
                              <a href={c.url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                                {c.url}
                              </a>
                              {c.snippet ? <div style={{ marginTop: 4 }}>{c.snippet}</div> : null}
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}

                  <div className="smallText" style={{ marginTop: 8 }}>
                    To confirm a candidate, use the “Discovered social profiles (confirm)” section below and click Analyze again.
                  </div>
                </>
              ) : null}
            </section>
          ) : null}

          {(data.social_candidates?.length ?? 0) > 0 ? (
            <section className="card">
              <div className="cardTitle">Discovered social profiles (confirm)</div>
              <div className="smallText" style={{ marginBottom: 10 }}>
                These are found via search snippets and may be ambiguous. Select the correct profile(s) and click Analyze
                again.
              </div>

              {(["instagram", "x", "medium"] as const).map((platform) => {
                const candidates = (data.social_candidates ?? []).filter((c) => c.platform === platform);
                if (candidates.length === 0) return null;
                const current = platform === "instagram" ? selectedInstagram : platform === "x" ? selectedX : selectedMedium;

                return (
                  <div key={platform} style={{ marginBottom: 14 }}>
                    <div className="kvLabel" style={{ textTransform: "capitalize" }}>
                      {platform}
                    </div>
                    <div style={{ display: "grid", gap: 8, marginTop: 6 }}>
                      <label style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                        <input
                          type="radio"
                          name={`pick-${platform}`}
                          checked={!current}
                          onChange={() => {
                            if (platform === "instagram") setSelectedInstagram("");
                            if (platform === "x") setSelectedX("");
                            if (platform === "medium") setSelectedMedium("");
                          }}
                        />
                        <span className="smallText">None / don’t use</span>
                      </label>
                      {candidates.map((c) => (
                        <label key={c.url} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                          <input
                            type="radio"
                            name={`pick-${platform}`}
                            checked={current === c.url}
                            onChange={() => {
                              if (platform === "instagram") setSelectedInstagram(c.url);
                              if (platform === "x") setSelectedX(c.url);
                              if (platform === "medium") setSelectedMedium(c.url);
                            }}
                          />
                          <span>
                            <div style={{ fontSize: 12, opacity: 0.8 }}>
                              confidence: {(c.confidence ?? 0).toFixed(2)}
                            </div>
                            <div style={{ marginTop: 2 }}>
                              <a href={c.url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                                {c.url}
                              </a>
                            </div>
                            {c.snippet ? <div style={{ marginTop: 4 }}>{c.snippet}</div> : null}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                );
              })}

              <div className="smallText" style={{ marginTop: 8 }}>
                Current selections: instagram={selectedInstagram || "—"} | x={selectedX || "—"} | medium={selectedMedium || "—"}
              </div>
            </section>
          ) : null}

          <section className="card">
            <div className="cardTitle">Company profile</div>
            <div>
              <strong>Summary:</strong> {data.company_profile?.summary ?? "unknown"}
            </div>
            <div style={{ height: 8 }} />
            <div>
              <strong>Likely products/services</strong>
              <ul className="list">
                {(data.company_profile?.likely_products_services ?? []).map((x, i) => (
                  <li key={i}>{x}</li>
                ))}
              </ul>
            </div>
            <div>
              <strong>Hiring signals</strong>
              <ul className="list">
                {(data.company_profile?.hiring_signals ?? []).map((x, i) => (
                  <li key={i}>{x}</li>
                ))}
              </ul>
            </div>
            <div>
              <strong>Recent public mentions</strong>
              <ul className="list">
                {(data.company_profile?.recent_public_mentions ?? []).map((x, i) => (
                  <li key={i}>{x}</li>
                ))}
              </ul>
            </div>
          </section>

          <section className="card">
            <div className="cardTitle">Study of Person (AI-inferred)</div>
            <ul className="list">
              <li>
                <strong>Likely role/focus:</strong> {data.study_of_person.likely_role_focus ?? "unknown"}
              </li>
              <li>
                <strong>Domain:</strong> {data.study_of_person.domain ?? "unknown"}
              </li>
              <li>
                <strong>Communication style:</strong> {data.study_of_person.communication_style ?? "unknown"}
              </li>
              <li>
                <strong>Seniority signal:</strong> {data.study_of_person.seniority_signal ?? "unknown"}
              </li>
              <li>
                <strong>Public presence:</strong> {data.study_of_person.public_presence_signal ?? "unknown"}
              </li>
            </ul>
          </section>

          <section className="card">
            <div className="cardTitle">Questions to ask</div>
            <ol className="list">
              {(data.questions_to_ask ?? []).map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ol>
          </section>

          <section className="card">
            <div className="cardTitle">Email openers</div>
            <ul className="list">
              <li>
                <strong>Formal:</strong> {data.email_openers?.formal ?? "unknown"}
              </li>
              <li>
                <strong>Warm:</strong> {data.email_openers?.warm ?? "unknown"}
              </li>
              <li>
                <strong>Technical:</strong> {data.email_openers?.technical ?? "unknown"}
              </li>
            </ul>
          </section>

          <section className="card">
            <div className="cardTitle">Red flags (avoid assumptions)</div>
            <ul className="list">
              {(data.red_flags ?? []).map((x, i) => (
                <li key={i}>{x}</li>
              ))}
            </ul>
          </section>

          {/* LinkedIn panel (snippets/evidence-based) */}
          {data.evidence?.some((e) => (e.url || "").includes("linkedin.com")) ? (
            <section className="card">
              <div className="cardTitle">LinkedIn (public snippets)</div>
              <ul className="list">
                {data.evidence
                  .filter((e) => (e.url || "").includes("linkedin.com"))
                  .slice(0, 5)
                  .map((e, i) => (
                    <li key={`li-${i}`} style={{ marginBottom: 10 }}>
                      <div style={{ marginTop: 6 }}>{e.snippet}</div>
                      {e.url ? (
                        <div style={{ marginTop: 4 }}>
                          <a href={e.url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                            {e.url}
                          </a>
                        </div>
                      ) : null}
                    </li>
                  ))}
              </ul>
            </section>
          ) : null}

          {/* GitHub panel */}
          {data.github_profile ? (
            <GitHubCard profile={data.github_profile} />
          ) : data.evidence?.some((e) => (e.url || "").includes("github.com")) ? (
            <section className="card">
              <div className="cardTitle">GitHub (public snippets)</div>
              <div className="smallText" style={{ marginBottom: 10 }}>
                GitHub API enrichment is unavailable right now; showing snippet-based evidence instead.
              </div>
              <ul className="list">
                {data.evidence
                  .filter((e) => (e.url || "").includes("github.com"))
                  .slice(0, 5)
                  .map((e, i) => (
                    <li key={`gh-${i}`} style={{ marginBottom: 10 }}>
                      <div style={{ marginTop: 6 }}>{e.snippet}</div>
                      {e.url ? (
                        <div style={{ marginTop: 4 }}>
                          <a href={e.url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                            {e.url}
                          </a>
                        </div>
                      ) : null}
                    </li>
                  ))}
              </ul>
            </section>
          ) : null}

          {/* Instagram panel */}
          {data.instagram_profile ? (
            <InstagramCard profile={data.instagram_profile} />
          ) : null}

          {/* Medium panel */}
          {data.medium_profile ? (
            <MediumCard profile={data.medium_profile} />
          ) : null}

          {/* X/Twitter panel */}
          {data.x_profile ? (
            <XCard profile={data.x_profile} />
          ) : null}

          <section className="card">
            <div className="cardTitle">Recommendations</div>

            <div className="twoCol">
              <div>
                <div>
                  <strong>Dress:</strong> {data.recommendations.dress ?? "—"}
                </div>
                <div>
                  <strong>Tone:</strong> {data.recommendations.tone ?? "—"}
                </div>

                <div style={{ height: 10 }} />

                <strong>Suggested agenda</strong>
                <ol className="list">
                  {data.recommendations.suggested_agenda.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ol>
              </div>

              <div>
                <strong>Connecting points</strong>
                <ul className="list">
                  {data.recommendations.connecting_points.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div style={{ height: 10 }} />

            <div className="twoCol">
              <div>
                <strong>Do</strong>
                <ul className="list">
                  {data.recommendations.dos.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
              <div>
                <strong>Don’t</strong>
                <ul className="list">
                  {data.recommendations.donts.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
            </div>
          </section>

          <section className="card">
            <div className="cardTitle">Evidence (public snippets)</div>
            <EvidenceBreakdownChart evidence={data.evidence} />
            {data.evidence.length === 0 ? (
              <div className="smallText">No evidence collected.</div>
            ) : (
              <ul className="list">
                {data.evidence.map((e, i) => (
                  <li key={i} style={{ marginBottom: 10 }}>
                    <div>
                      <span className="pill" style={{ textTransform: "none" }}>
                        {e.source}
                      </span>
                    </div>
                    <div style={{ marginTop: 6 }}>{e.snippet}</div>
                    {e.url ? (
                      <div style={{ marginTop: 4 }}>
                        <a href={e.url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                          {e.url}
                        </a>
                      </div>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}

            <JsonDetails title="Raw JSON response" data={data} />
          </section>
        </div> : <MrAssistant analyze={data} />}
        </>
      ) : null}
      </div>
    </div>
  );
}

export default App;
