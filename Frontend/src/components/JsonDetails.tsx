export function JsonDetails({ title, data }: { title: string; data: unknown }) {
  return (
    <details className="details">
      <summary style={{ cursor: "pointer", color: "rgb(17, 94, 89)", fontWeight: 900 }}>{title}</summary>
      <div style={{ marginTop: 10 }}>
        <pre
          style={{
            padding: 12,
            borderRadius: 12,
            border: "1px solid #e5e7eb",
            background: "#f1f5f9",
            overflowX: "auto",
          }}
        >
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </details>
  );
}
