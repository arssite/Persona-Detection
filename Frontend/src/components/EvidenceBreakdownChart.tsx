import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { EvidenceItem } from "../api/client";

function groupCounts(evidence: EvidenceItem[]) {
  const map = new Map<string, number>();
  for (const e of evidence) {
    const k = e.source || "unknown";
    map.set(k, (map.get(k) ?? 0) + 1);
  }
  return Array.from(map.entries()).map(([source, count]) => ({ source, count }));
}

export function EvidenceBreakdownChart({ evidence }: { evidence: EvidenceItem[] }) {
  const data = groupCounts(evidence);

  if (!evidence.length) return null;

  return (
    <div style={{ height: 220 }}>
      <div style={{ fontSize: 12, color: "#475569", marginBottom: 8 }}>Evidence sources (count)</div>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="source"
            interval={0}
            angle={-12}
            textAnchor="end"
            height={55}
            tick={{ fill: "#475569", fontSize: 12 }}
            axisLine={{ stroke: "#cbd5e1" }}
            tickLine={{ stroke: "#cbd5e1" }}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fill: "#475569", fontSize: 12 }}
            axisLine={{ stroke: "#cbd5e1" }}
            tickLine={{ stroke: "#cbd5e1" }}
          />
          <Tooltip
            contentStyle={{ borderRadius: 10, border: "1px solid #e5e7eb", background: "#ffffff" }}
            cursor={{ fill: "rgba(125, 249, 255, 0.18)" }}
          />
          <Bar dataKey="count" fill="rgb(17, 94, 89)" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
