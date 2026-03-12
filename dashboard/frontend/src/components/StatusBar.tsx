import { useEffect, useState } from "react";
import { api, Project, Status } from "../lib/api";

interface Props {
  status: Status | null;
  onProjectChange: (path: string) => void;
}

export function StatusBar({ status, onProjectChange }: Props) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api.getProjects().then(setProjects).catch(console.error);
  }, []);

  const totalQ = status
    ? status.questions.PENDING +
      status.questions.DONE +
      status.questions.INCONCLUSIVE +
      status.questions.IN_PROGRESS
    : 0;

  const lastMod = status?.last_modified
    ? new Date(status.last_modified).toLocaleString()
    : "—";

  return (
    <div className="flex items-center gap-6 px-6 py-3 bg-[#1e1b2e] border-b border-white/10 flex-wrap">
      {/* Project name + switcher */}
      <div className="relative">
        <button
          onClick={() => setOpen((o) => !o)}
          className="flex items-center gap-2 text-xl font-semibold text-[#e5e7eb] hover:text-[#38bdf8] transition-colors"
        >
          {status?.project ?? "…"}
          <span className="text-xs text-[#9ca3af] mt-0.5">▾</span>
        </button>
        {open && projects.length > 0 && (
          <div className="absolute top-full left-0 mt-1 z-50 bg-[#2d2a3e] border border-white/10 rounded-md shadow-xl min-w-[200px]">
            {projects.map((p) => (
              <button
                key={p.path}
                onClick={() => {
                  onProjectChange(p.path);
                  setOpen(false);
                }}
                className="block w-full text-left px-4 py-2 text-sm text-[#e5e7eb] hover:bg-white/10 transition-colors"
              >
                {p.name}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="h-5 w-px bg-white/10" />

      {/* Questions */}
      <div className="text-sm text-[#9ca3af]">
        Questions:{" "}
        <span className="text-[#e5e7eb] font-medium">
          {status?.questions.DONE ?? 0} done
        </span>
        {" / "}
        <span className="text-[#e5e7eb] font-medium">{totalQ}</span> total
        {(status?.questions.PENDING ?? 0) > 0 && (
          <span className="ml-2 text-[#9ca3af]">
            ({status!.questions.PENDING} pending)
          </span>
        )}
      </div>

      <div className="h-5 w-px bg-white/10" />

      {/* Verdict pills */}
      <div className="flex items-center gap-3 text-sm">
        <span className="text-[#ef4444]">
          🔴 {status?.verdicts.FAILURE ?? 0} FAILURE
        </span>
        <span className="text-[#f59e0b]">
          🟡 {status?.verdicts.WARNING ?? 0} WARNING
        </span>
        <span className="text-[#34d399]">
          🟢 {status?.verdicts.HEALTHY ?? 0} HEALTHY
        </span>
        {(status?.verdicts.INCONCLUSIVE ?? 0) > 0 && (
          <span className="text-[#9ca3af]">
            ⬜ {status!.verdicts.INCONCLUSIVE} INCONCLUSIVE
          </span>
        )}
      </div>

      <div className="ml-auto text-xs text-[#9ca3af]">Updated: {lastMod}</div>
    </div>
  );
}
