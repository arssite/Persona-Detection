import { useMemo, useState } from "react";
import "./App.css";
import { analyze, type AnalyzeResponse } from "./api/client";
import { ConfidenceBadge } from "./components/ConfidenceBadge";
import { ConfidenceMeter } from "./components/ConfidenceMeter";
import { EvidenceBreakdownChart } from "./components/EvidenceBreakdownChart";
import { JsonDetails } from "./components/JsonDetails";
import { BubbleLoader } from "./components/BubbleLoader";
import { UseCasesRotator } from "./components/UseCasesRotator";
import { Card } from "./components/Card";
import { GitHubCard } from "./components/GitHubCard";

function App() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalyzeResponse | null>(null);

  const canSubmit = useMemo(() => email.trim().length > 5 && email.includes("@"), [email]);

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

      const res = await analyze({ email: email.trim() });
      window.clearTimeout(t1);
      window.clearTimeout(t2);
      window.clearTimeout(t3);
      setStage(null);
      setData(res);
    } catch (err) {
      setStage(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="pageTitle">Meeting Intelligence MVP</h1>
      <p className="subtitle">Enter a corporate email. We infer meeting guidance using public web signals and Gemini.</p>

      <form onSubmit={onSubmit} className="topBar">
        <input
          className="input"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="firstname.lastname@company.com"
        />
        <button disabled={!canSubmit || loading} type="submit" className="button">
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
        <div className="grid">
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

          {data.github_profile ? <GitHubCard profile={data.github_profile} /> : null}

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
        </div>
      ) : null}
    </div>
  );
}

export default App;
