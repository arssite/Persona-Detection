import { useMemo, useState } from "react";
import type { AnalyzeResponse, EvidenceItem } from "../api/client";
import { assistantBootstrap, assistantChat, type AssistantBootstrapResponse } from "../api/client";
import { Card } from "./Card";

type ChatMsg = { role: "user" | "assistant"; content: string };

function EvidenceList({ evidence }: { evidence: EvidenceItem[] }) {
  if (!evidence?.length) return null;
  return (
    <ul className="list">
      {evidence.map((e, i) => (
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
  );
}

export function MrAssistant({ analyze }: { analyze: AnalyzeResponse }) {
  const [showInfo, setShowInfo] = useState(false);

  const [pitch, setPitch] = useState("");
  const [goal, setGoal] = useState("");
  const [meetingType, setMeetingType] = useState<string>("intro call");
  const [audienceContext, setAudienceContext] = useState("");
  const [constraints, setConstraints] = useState("");

  const [boot, setBoot] = useState<AssistantBootstrapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [chatInput, setChatInput] = useState("");
  const [chat, setChat] = useState<ChatMsg[]>([]);

  const [pendingRefreshConfirm, setPendingRefreshConfirm] = useState<
    { sessionId: string; originalMessage: string; reason?: string | null } | null
  >(null);

  const canBootstrap = useMemo(() => pitch.trim().length > 3 && goal.trim().length > 3, [pitch, goal]);

  async function onBootstrap() {
    setError(null);
    setLoading(true);
    try {
      const res = await assistantBootstrap({
        email: analyze.input_email,
        agenda: {
          pitch: pitch.trim(),
          goal: goal.trim(),
          meeting_type: meetingType,
          audience_context: audienceContext.trim() || null,
          constraints: constraints.trim() || null,
        },
        refresh_public_signals: false,
      });
      setBoot(res);
      setChat([
        { role: "assistant" as const, content: res.intro },
        ...(res.starter_questions?.length
          ? [
              {
                role: "assistant" as const,
                content: `Here are 5 strong starter questions:\n- ${res.starter_questions.join("\n- ")}`,
              },
            ]
          : []),
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function sendMessage(opts?: { confirm_refresh?: boolean }) {
    if (!boot) return;
    const msg = chatInput.trim();
    if (!msg) return;

    setError(null);
    setPendingRefreshConfirm(null);
    setChatInput("");
    setChat((c) => [...c, { role: "user", content: msg }]);
    setLoading(true);

    try {
      const res = await assistantChat({
        session_id: boot.session_id,
        message: msg,
        confirm_refresh: Boolean(opts?.confirm_refresh),
      });

      if (res.refresh_recommended) {
        setPendingRefreshConfirm({ sessionId: res.session_id, originalMessage: msg, reason: res.refresh_reason });
      }

      setChat((c) => [...c, { role: "assistant", content: res.message }]);

      if (res.follow_up_questions?.length) {
        setChat((c) => [
          ...c,
          {
            role: "assistant",
            content: `Quick follow-ups to tailor this:\n- ${res.follow_up_questions.join("\n- ")}`,
          },
        ]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function confirmRefresh() {
    if (!pendingRefreshConfirm || !boot) return;
    // Re-send the exact same question with confirm_refresh.
    setChat((c) => [...c, { role: "assistant", content: "Refreshing public signals… (bounded search + crawl)" }]);
    setLoading(true);
    try {
      const res = await assistantChat({
        session_id: boot.session_id,
        message: pendingRefreshConfirm.originalMessage,
        confirm_refresh: true,
      });
      setPendingRefreshConfirm(null);
      setChat((c) => [...c, { role: "assistant", content: res.message }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div className="cardTitle" style={{ marginBottom: 4 }}>
            Mr Assistant (RAG agent)
          </div>
          <div className="smallText">Ask follow-up questions and get pitch coaching grounded in public evidence.</div>
        </div>
        <button className="button" type="button" onClick={() => setShowInfo(true)} style={{ padding: "8px 12px" }}>
          i
        </button>
      </div>

      {showInfo ? (
        <div className="modalOverlay" role="dialog" aria-modal="true">
          <div className="modal">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div className="cardTitle">Mr Assistant — Features</div>
              <button className="button" type="button" onClick={() => setShowInfo(false)} style={{ padding: "6px 10px" }}>
                Close
              </button>
            </div>
            <div style={{ height: 8 }} />
            <ul className="list">
              <li>Generates <strong>5 starter questions</strong> tailored to the target persona + your agenda.</li>
              <li>Helps you craft a <strong>30/60/120s pitch</strong> and meeting talk-track.</li>
              <li>Suggests <strong>likely objections</strong> and how to respond.</li>
              <li>Answers ad-hoc questions with <strong>evidence + confidence</strong> (public signals only).</li>
              <li>Can <strong>refresh public signals</strong> (bounded search + crawl) <em>only after your confirmation</em>.</li>
            </ul>
            <div className="note" style={{ marginTop: 10 }}>
              Safety: outputs are suggestions, not facts. Mr Assistant will avoid inventing claims and will recommend refresh when needed.
            </div>
          </div>
        </div>
      ) : null}

      {!boot ? (
        <Card title="Start (tell Mr Assistant your agenda)">
          <div className="twoCol">
            <div>
              <div className="kvLabel">What are you pitching / offering?</div>
              <textarea className="input" style={{ minHeight: 72 }} value={pitch} onChange={(e) => setPitch(e.target.value)} />

              <div style={{ height: 10 }} />

              <div className="kvLabel">What’s your goal for the meeting?</div>
              <textarea className="input" style={{ minHeight: 72 }} value={goal} onChange={(e) => setGoal(e.target.value)} />
            </div>

            <div>
              <div className="kvLabel">Meeting type</div>
              <select className="input" value={meetingType} onChange={(e) => setMeetingType(e.target.value)}>
                <option value="intro call">Intro call</option>
                <option value="discovery">Discovery</option>
                <option value="technical deep dive">Technical deep dive</option>
                <option value="negotiation">Negotiation</option>
                <option value="other">Other</option>
              </select>

              <div style={{ height: 10 }} />

              <div className="kvLabel">Audience context (optional)</div>
              <textarea
                className="input"
                style={{ minHeight: 72 }}
                value={audienceContext}
                onChange={(e) => setAudienceContext(e.target.value)}
                placeholder="E.g., they care about ROI, security, headcount, or timeline…"
              />

              <div style={{ height: 10 }} />

              <div className="kvLabel">Constraints (optional)</div>
              <textarea
                className="input"
                style={{ minHeight: 72 }}
                value={constraints}
                onChange={(e) => setConstraints(e.target.value)}
                placeholder="Budget / timeline / compliance / pricing boundaries…"
              />
            </div>
          </div>

          <div style={{ height: 12 }} />
          <button className="button" type="button" disabled={!canBootstrap || loading} onClick={onBootstrap}>
            {loading ? "Starting…" : "Start with Mr Assistant"}
          </button>
          {error ? <pre className="error">{error}</pre> : null}
        </Card>
      ) : (
        <>
          <Card title="Session">
            <div className="smallText">
              Target: <strong>{boot.analyze_snapshot.person_name_guess ?? "Unknown"}</strong> @ <strong>{boot.analyze_snapshot.company_domain ?? "Unknown"}</strong>
            </div>

            <div style={{ height: 12 }} />

            <div className="chatPanel">
              {chat.map((m, idx) => (
                <div key={idx} className={m.role === "user" ? "chatMsg chatUser" : "chatMsg chatAssistant"}>
                  <div className="chatRole">{m.role === "user" ? "You" : "Mr Assistant"}</div>
                  <div className="chatContent">{m.content}</div>
                </div>
              ))}
            </div>

            <div style={{ height: 10 }} />

            {pendingRefreshConfirm ? (
              <div className="note">
                <div style={{ marginBottom: 8 }}>
                  <strong>Refresh recommended:</strong> {pendingRefreshConfirm.reason ?? "This may need up-to-date public info."}
                </div>
                <button className="button" type="button" onClick={confirmRefresh} disabled={loading}>
                  {loading ? "Refreshing…" : "Confirm refresh & answer"}
                </button>
              </div>
            ) : null}

            <div className="chatComposer">
              <input
                className="input"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask: how should I pitch this? what questions to ask? handle objections?"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    void sendMessage();
                  }
                }}
              />
              <button className="button" type="button" disabled={loading || !chatInput.trim()} onClick={() => void sendMessage()}>
                {loading ? "Sending…" : "Send"}
              </button>
            </div>

            {error ? <pre className="error">{error}</pre> : null}
          </Card>

          <Card title="Citations (public evidence)">
            <EvidenceList evidence={boot.citations} />
          </Card>
        </>
      )}
    </div>
  );
}
