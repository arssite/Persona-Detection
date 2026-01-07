import { useEffect, useState } from "react";

const USE_CASES = [
  {
    title: "Recruiter / Hiring Manager prep",
    body: "Get a quick persona + conversation angles before a screening call.",
  },
  {
    title: "Sales discovery call",
    body: "Tailor your pitch tone, agenda, and connecting points based on public signals.",
  },
  {
    title: "Customer success / QBR",
    body: "Walk into meetings with suggested agenda items and do/don’t guidance.",
  },
  {
    title: "Investor / partner intro",
    body: "Align quickly on what the company likely cares about and where you can add value.",
  },
] as const;

export function UseCasesRotator() {
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    const t = window.setInterval(() => setIdx((x) => (x + 1) % USE_CASES.length), 2200);
    return () => window.clearInterval(t);
  }, []);

  const item = USE_CASES[idx];

  return (
    <div className="useCase">
      <div className="useCaseTitle">{item.title}</div>
      <div className="useCaseBody">{item.body}</div>
    </div>
  );
}
