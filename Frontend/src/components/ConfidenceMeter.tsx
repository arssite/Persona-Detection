import type { AnalyzeResponse } from "../api/client";

function labelToScore(label: AnalyzeResponse["confidence"]["label"]) {
  if (label === "high") return 0.85;
  if (label === "medium") return 0.55;
  return 0.25;
}

export function ConfidenceMeter({ confidence }: { confidence: AnalyzeResponse["confidence"] }) {
  const score = labelToScore(confidence.label);
  const pct = Math.round(score * 100);

  const color =
    confidence.label === "high" ? "rgb(17, 94, 89)" : confidence.label === "medium" ? "rgb(125, 249, 255)" : "rgb(170, 255, 0)";

  return (
    <div style={{ display: "grid", gap: 8 }}>
      <div style={{ fontSize: 12, color: "#475569" }}>Confidence meter</div>
      <div style={{ height: 10, borderRadius: 999, background: "#e5e7eb", overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color }} />
      </div>
      <div style={{ fontSize: 12, color: "#374151" }}>{pct}% (mapped from {confidence.label})</div>
    </div>
  );
}
