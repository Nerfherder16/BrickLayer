const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8100";

function projectParam(): string {
  const params = new URLSearchParams(window.location.search);
  const p = params.get("project");
  return p ? `?project=${encodeURIComponent(p)}` : "";
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}${projectParam()}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const sep = path.includes("?") ? "&" : "?";
  const pp = projectParam().replace("?", sep);
  const res = await fetch(`${BASE_URL}${path}${pp}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json();
}

export interface Status {
  project: string;
  project_path: string;
  questions: {
    PENDING: number;
    DONE: number;
    INCONCLUSIVE: number;
    IN_PROGRESS: number;
  };
  verdicts: {
    FAILURE: number;
    WARNING: number;
    HEALTHY: number;
    INCONCLUSIVE: number;
  };
  last_modified: string | null;
}

export interface Question {
  id: string;
  title: string;
  status: "PENDING" | "DONE" | "INCONCLUSIVE" | "IN_PROGRESS";
  domain: string;
  hypothesis: string | null;
}

export interface Finding {
  id: string;
  title: string;
  verdict: "FAILURE" | "WARNING" | "HEALTHY" | "INCONCLUSIVE" | "UNKNOWN";
  severity: string;
  has_correction: boolean;
  modified: string;
}

export interface FindingDetail {
  id: string;
  content: string;
}

export interface Project {
  name: string;
  path: string;
}

export interface ResultRow {
  commit: string;
  question_id: string;
  verdict: string;
  treasury_runway_months: string;
  key_finding: string;
  scenario_name: string;
}

export const api = {
  getStatus: () => get<Status>("/api/status"),
  getQuestions: () => get<Question[]>("/api/questions"),
  addQuestion: (body: {
    question: string;
    domain: string;
    hypothesis: string;
    priority: "next" | "end";
  }) => post<{ ok: boolean; id: string }>("/api/questions", body),
  getFindings: () => get<Finding[]>("/api/findings"),
  getFinding: (id: string) => get<FindingDetail>(`/api/findings/${id}`),
  correctFinding: (id: string, correction: string) =>
    post<{ ok: boolean }>(`/api/findings/${id}/correct`, { correction }),
  getProjects: () => get<Project[]>("/api/projects"),
  getResults: () => get<ResultRow[]>("/api/results"),
};
