import type { AnalyzeResponse } from "../api/client";

export function ConfidenceBadge({ confidence }: { confidence: AnalyzeResponse["confidence"] }) {
  const color =
    confidence.label === "high" ? "#0f766e" : confidence.label === "medium" ? "#b45309" : "#b91c1c";

  return (
    <div style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
      <span
        style={{
          padding: "4px 10px",
          borderRadius: 999,
          background: color,
          color: "white",
          fontSize: 12,
          fontWeight: 600,
          textTransform: "uppercase",
        }}
      >
        {confidence.label}
      </span>
      <span style={{ fontSize: 12, color: "#374151" }}>{confidence.rationale}</span>
    </div>
  );
}
