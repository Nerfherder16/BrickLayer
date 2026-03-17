import { useEffect, useState } from "react";
import { api, AgentInfo } from "../lib/api";

const MODEL_STYLE: Record<
  string,
  { badge: string; dot: string; label: string }
> = {
  opus: {
    badge: "bg-[#2e1065] text-[#a78bfa] border border-[#7c3aed]/30",
    dot: "bg-[#8b5cf6]",
    label: "Opus",
  },
  sonnet: {
    badge: "bg-[#0c2340] text-[#38bdf8] border border-[#0284c7]/30",
    dot: "bg-[#38bdf8]",
    label: "Sonnet",
  },
  haiku: {
    badge: "bg-[#064e3b] text-[#34d399] border border-[#059669]/30",
    dot: "bg-[#34d399]",
    label: "Haiku",
  },
  "": {
    badge: "bg-[#1f2937] text-[#6b7280] border border-white/10",
    dot: "bg-[#4b5563]",
    label: "—",
  },
};

const TIER_ORDER = ["opus", "sonnet", "haiku", ""];

interface Props {
  onRefresh: () => void;
}

export function AgentFleet({ onRefresh: _ }: Props) {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("ALL");

  useEffect(() => {
    api
      .getAgents()
      .then(setAgents)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const sorted = [...agents].sort((a, b) => {
    const ta = TIER_ORDER.indexOf(a.model);
    const tb = TIER_ORDER.indexOf(b.model);
    if (ta !== tb) return ta - tb;
    return a.name.localeCompare(b.name);
  });

  const filtered =
    filter === "ALL" ? sorted : sorted.filter((a) => a.model === filter);

  const counts = agents.reduce<Record<string, number>>((acc, a) => {
    const k = a.model || "";
    acc[k] = (acc[k] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <h2 className="text-sm font-semibold text-[#e5e7eb] uppercase tracking-wide">
          Agent Fleet ({agents.length})
        </h2>
        {/* Tier filter pills */}
        <div className="flex items-center gap-1">
          {(["ALL", "opus", "sonnet", "haiku"] as const).map((t) => {
            const style = t === "ALL" ? null : MODEL_STYLE[t];
            const count = t === "ALL" ? agents.length : (counts[t] ?? 0);
            return (
              <button
                key={t}
                onClick={() => setFilter(t)}
                className={`text-xs px-2 py-0.5 rounded-full font-medium transition border ${
                  filter === t
                    ? style
                      ? style.badge
                      : "bg-white/10 text-[#e5e7eb] border-white/20"
                    : "bg-transparent text-[#6b7280] border-transparent hover:text-[#9ca3af]"
                }`}
              >
                {t === "ALL" ? "All" : MODEL_STYLE[t].label} {count}
              </button>
            );
          })}
        </div>
      </div>

      {/* Agent list */}
      <div className="flex-1 overflow-auto px-4 py-3 space-y-1.5">
        {loading && (
          <p className="text-xs text-[#4b5563] py-8 text-center">
            Loading agents…
          </p>
        )}
        {!loading && filtered.length === 0 && (
          <p className="text-xs text-[#4b5563] py-8 text-center">
            No agents found
          </p>
        )}
        {filtered.map((agent) => {
          const style = MODEL_STYLE[agent.model] ?? MODEL_STYLE[""];
          return (
            <div
              key={agent.name}
              className="flex items-start gap-3 px-3 py-2.5 rounded-md bg-[#1e1b2e] border border-white/[0.06] hover:border-white/10 transition-colors"
            >
              {/* Model dot */}
              <span
                className={`mt-1 w-2 h-2 rounded-full shrink-0 ${style.dot}`}
              />

              {/* Name + description */}
              <div className="flex-1 min-w-0">
                <span className="text-sm font-medium text-[#e5e7eb] font-mono">
                  {agent.name}
                </span>
                {agent.description && (
                  <p className="text-xs text-[#6b7280] mt-0.5 leading-snug line-clamp-2">
                    {agent.description}
                  </p>
                )}
              </div>

              {/* Model badge */}
              <span
                className={`text-xs px-2 py-0.5 rounded font-medium shrink-0 ${style.badge}`}
              >
                {style.label || "?"}
              </span>
            </div>
          );
        })}
      </div>

      {/* Tier summary footer */}
      {!loading && agents.length > 0 && (
        <div className="flex items-center gap-4 px-4 py-2 border-t border-white/5 text-xs text-[#6b7280]">
          {(["opus", "sonnet", "haiku"] as const).map((t) => (
            <span key={t} className="flex items-center gap-1">
              <span
                className={`w-1.5 h-1.5 rounded-full ${MODEL_STYLE[t].dot}`}
              />
              <span className={MODEL_STYLE[t].badge.split(" ")[1]}>
                {MODEL_STYLE[t].label}
              </span>{" "}
              {counts[t] ?? 0}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
