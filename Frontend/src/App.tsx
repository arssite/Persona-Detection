import { useMemo, useState } from "react";
import "./App.css";
import { analyze, type AnalyzeResponse } from "./api/client";
import { ConfidenceBadge } from "./components/ConfidenceBadge";

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
    <div style={{ maxWidth: 920, margin: "40px auto", padding: 16 }}>
      <h1 style={{ marginBottom: 8 }}>Meeting Intelligence MVP</h1>
      <p style={{ marginTop: 0, color: "#4b5563" }}>
        Enter a corporate email. We infer meeting guidance using public web signals and Gemini.
      </p>

      <form onSubmit={onSubmit} style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="firstname.lastname@company.com"
          style={{ flex: 1, padding: 12, borderRadius: 8, border: "1px solid #d1d5db" }}
        />
        <button
          disabled={!canSubmit || loading}
          type="submit"
          style={{
            padding: "12px 16px",
            borderRadius: 8,
            border: "1px solid #111827",
            background: loading ? "#9ca3af" : "#111827",
            color: "white",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      <div style={{ marginTop: 10, fontSize: 12, color: "#6b7280" }}>
        Note: This tool uses public information and produces AI-inferred suggestions, not facts.
      </div>

      {loading && stage ? (
        <div style={{ marginTop: 14, fontSize: 14, color: "#374151" }}>
          <strong>Status:</strong> {stage}
        </div>
      ) : null}

      {error ? (
        <pre
          style={{
            marginTop: 16,
            padding: 12,
            background: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: 8,
            color: "#991b1b",
            whiteSpace: "pre-wrap",
          }}
        >
          {error}
        </pre>
      ) : null}

      {data ? (
        <div style={{ marginTop: 22, display: "grid", gap: 16 }}>
          <div style={{ padding: 16, border: "1px solid #e5e7eb", borderRadius: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
              <div>
                <div style={{ fontSize: 14, color: "#6b7280" }}>Input</div>
                <div style={{ fontWeight: 600 }}>{data.input_email}</div>
                <div style={{ marginTop: 6, fontSize: 14, color: "#374151" }}>
                  <div>
                    <strong>Name guess:</strong> {data.person_name_guess ?? "—"}
                  </div>
                  <div>
                    <strong>Company domain:</strong> {data.company_domain ?? "—"}
                  </div>
                </div>
              </div>
              <div>
                <div style={{ fontSize: 14, color: "#6b7280" }}>Confidence</div>
                <div style={{ marginTop: 6 }}>
                  <ConfidenceBadge confidence={data.confidence} />
                </div>
              </div>
            </div>
          </div>

          <div style={{ padding: 16, border: "1px solid #e5e7eb", borderRadius: 12 }}>
            <h2 style={{ marginTop: 0 }}>Study of Person (AI-inferred)</h2>
            <ul style={{ margin: 0 }}>
              <li>
                <strong>Likely role/focus:</strong> {data.study_of_person.likely_role_focus ?? "—"}
              </li>
              <li>
                <strong>Domain:</strong> {data.study_of_person.domain ?? "—"}
              </li>
              <li>
                <strong>Communication style:</strong> {data.study_of_person.communication_style ?? "—"}
              </li>
            </ul>
          </div>

          <div style={{ padding: 16, border: "1px solid #e5e7eb", borderRadius: 12 }}>
            <h2 style={{ marginTop: 0 }}>Recommendations</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <div>
                  <strong>Dress:</strong> {data.recommendations.dress ?? "—"}
                </div>
                <div>
                  <strong>Tone:</strong> {data.recommendations.tone ?? "—"}
                </div>
              </div>
              <div>
                <div>
                  <strong>Connecting points:</strong>
                  <ul>
                    {data.recommendations.connecting_points.map((x, i) => (
                      <li key={i}>{x}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <strong>Do</strong>
                <ul>
                  {data.recommendations.dos.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
              <div>
                <strong>Don’t</strong>
                <ul>
                  {data.recommendations.donts.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div>
              <strong>Suggested agenda</strong>
              <ol>
                {data.recommendations.suggested_agenda.map((x, i) => (
                  <li key={i}>{x}</li>
                ))}
              </ol>
            </div>
          </div>

          <div style={{ padding: 16, border: "1px solid #e5e7eb", borderRadius: 12 }}>
            <h2 style={{ marginTop: 0 }}>Evidence (public snippets)</h2>
            {data.evidence.length === 0 ? (
              <div style={{ color: "#6b7280" }}>No evidence collected yet (backend scaffold).</div>
            ) : (
              <ul>
                {data.evidence.map((e, i) => (
                  <li key={i}>
                    <strong>{e.source}:</strong> {e.snippet} {e.url ? <a href={e.url}>link</a> : null}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default App;
