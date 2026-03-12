import { useCallback, useEffect, useState } from "react";
import { api, Finding, Question, Status } from "./lib/api";
import { StatusBar } from "./components/StatusBar";
import { QuestionQueue } from "./components/QuestionQueue";
import { FindingFeed } from "./components/FindingFeed";

function getProjectFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get("project");
}

function setProjectInUrl(path: string) {
  const url = new URL(window.location.href);
  url.searchParams.set("project", path);
  window.history.replaceState(null, "", url.toString());
}

export default function App() {
  const [status, setStatus] = useState<Status | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, q, f] = await Promise.all([
        api.getStatus(),
        api.getQuestions(),
        api.getFindings(),
      ]);
      setStatus(s);
      setQuestions(q);
      setFindings(f);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 10_000);
    return () => clearInterval(interval);
  }, [refresh]);

  const handleProjectChange = (path: string) => {
    setProjectInUrl(path);
    refresh();
  };

  return (
    <div
      className="min-h-screen bg-[#0f0d1a] text-[#e5e7eb] flex flex-col"
      style={{ fontFamily: "'Space Grotesk', sans-serif" }}
    >
      <StatusBar status={status} onProjectChange={handleProjectChange} />

      {error && (
        <div className="px-6 py-2 bg-[#450a0a] border-b border-[#ef4444]/30 text-sm text-[#ef4444]">
          Error: {error} — is the backend running on port 8100?
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Left: Question Queue — 60% */}
        <div className="w-[60%] border-r border-white/10 overflow-hidden flex flex-col">
          <QuestionQueue questions={questions} onRefresh={refresh} />
        </div>

        {/* Right: Finding Feed — 40% */}
        <div className="w-[40%] overflow-hidden flex flex-col">
          <FindingFeed findings={findings} onRefresh={refresh} />
        </div>
      </div>
    </div>
  );
}
