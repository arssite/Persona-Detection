import type { AnalyzeResponse } from "../api/client";

export function ConfidenceBadge({ confidence }: { confidence: AnalyzeResponse["confidence"] }) {
  return (
    <div style={{ display: "grid", gap: 8 }}>
      <div style={{ display: "inline-flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <span className="badge">{confidence.label}</span>
        <span className="smallText">{confidence.rationale}</span>
      </div>
    </div>
  );
}
