import { useCallback, useEffect, useState } from "react";
import { api, Finding, Question, Status } from "./lib/api";
import { StatusBar } from "./components/StatusBar";
import { QuestionQueue } from "./components/QuestionQueue";
import { FindingFeed } from "./components/FindingFeed";
import { AgentFleet } from "./components/AgentFleet";

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
  const [rightTab, setRightTab] = useState<"findings" | "agents">("findings");

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

  // C-16: adaptive polling — 3s when a campaign is active, 10s when idle
  const isActive = questions.some((q) => q.status === "IN_PROGRESS");

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, isActive ? 3_000 : 10_000);
    return () => clearInterval(interval);
  }, [refresh, isActive]);

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

        {/* Right: tabbed panel (Findings | Agents) — 40% */}
        <div className="w-[40%] overflow-hidden flex flex-col">
          {/* Tab bar */}
          <div className="flex items-center gap-1 px-3 py-2 border-b border-white/10 bg-[#13111c]">
            <button
              onClick={() => setRightTab("findings")}
              className={`text-xs px-3 py-1 rounded font-medium transition ${
                rightTab === "findings"
                  ? "bg-[#38bdf8] text-[#0f0d1a]"
                  : "text-[#9ca3af] hover:text-[#e5e7eb] hover:bg-white/5"
              }`}
            >
              Findings
            </button>
            <button
              onClick={() => setRightTab("agents")}
              className={`text-xs px-3 py-1 rounded font-medium transition ${
                rightTab === "agents"
                  ? "bg-[#8b5cf6] text-white"
                  : "text-[#9ca3af] hover:text-[#e5e7eb] hover:bg-white/5"
              }`}
            >
              Agents
            </button>
          </div>
          {rightTab === "findings" ? (
            <FindingFeed findings={findings} onRefresh={refresh} />
          ) : (
            <AgentFleet onRefresh={refresh} />
          )}
        </div>
      </div>
    </div>
  );
}
