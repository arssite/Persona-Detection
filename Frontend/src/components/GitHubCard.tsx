import type { AnalyzeResponse } from "../api/client";
import { Card } from "./Card";

export function GitHubCard({ profile }: { profile: NonNullable<AnalyzeResponse["github_profile"]> }) {
  return (
    <Card title="GitHub (public signals)">
      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <strong>User:</strong> {profile.username} {profile.html_url ? <a href={profile.html_url} target="_blank" rel="noreferrer">link</a> : null}
        </div>
        <div className="smallText">
          {profile.bio ?? ""}
        </div>
        {profile.top_languages?.length ? (
          <div>
            <strong>Top languages:</strong> {profile.top_languages.join(", ")}
          </div>
        ) : null}
        {profile.top_repos?.length ? (
          <div>
            <strong>Recent repos:</strong>
            <ul className="list">
              {profile.top_repos.map((r, i) => (
                <li key={i}>
                  {r.html_url ? (
                    <a href={r.html_url} target="_blank" rel="noreferrer">
                      {r.name ?? r.html_url}
                    </a>
                  ) : (
                    r.name
                  )}
                  {r.language ? <span className="smallText"> — {r.language}</span> : null}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
