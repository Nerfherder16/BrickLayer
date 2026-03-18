import { useState } from "react";
import { api, Finding, FindingDetail } from "../lib/api";

interface Props {
  findings: Finding[];
  onRefresh: () => void;
}

const VERDICT_COLORS: Record<string, string> = {
  FAILURE: "bg-[#450a0a] text-[#ef4444]",
  WARNING: "bg-[#451a03] text-[#f59e0b]",
  HEALTHY: "bg-[#064e3b] text-[#34d399]",
  INCONCLUSIVE: "bg-[#1f2937] text-[#9ca3af]",
  UNKNOWN: "bg-[#1f2937] text-[#9ca3af]",
};

interface CardProps {
  finding: Finding;
  onCorrect: () => void;
}

function FindingCard({ finding, onCorrect }: CardProps) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState<FindingDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [showCorrect, setShowCorrect] = useState(false);
  const [correction, setCorrection] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const toggleExpand = async () => {
    if (!expanded && !detail) {
      setLoadingDetail(true);
      try {
        const d = await api.getFinding(finding.id);
        setDetail(d);
      } catch (e) {
        console.error(e);
      } finally {
        setLoadingDetail(false);
      }
    }
    setExpanded((e) => !e);
  };

  const submitCorrection = async () => {
    if (!correction.trim()) return;
    setSubmitting(true);
    try {
      await api.correctFinding(finding.id, correction);
      setShowCorrect(false);
      setCorrection("");
      onCorrect();
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="border border-white/10 rounded-md bg-[#1e1b2e] overflow-hidden">
      {/* Card header */}
      <div
        className="flex items-start gap-3 px-4 py-3 cursor-pointer hover:bg-white/[0.03] transition-colors"
        onClick={toggleExpand}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`text-xs px-2 py-0.5 rounded font-medium ${VERDICT_COLORS[finding.verdict]}`}
            >
              {finding.verdict}
            </span>
            {finding.has_correction && (
              <span className="text-xs px-2 py-0.5 rounded bg-[#312e81] text-[#818cf8] font-medium">
                Corrected
              </span>
            )}
            {finding.needs_human && (
              <span className="text-xs px-2 py-0.5 rounded bg-[#451a03] text-[#f59e0b] font-medium border border-[#f59e0b]/20">
                ⚠ Human
              </span>
            )}
            <span className="text-xs text-[#4b5563]">{finding.id}</span>
          </div>
          {finding.confidence != null && (
            <div className="mt-1">
              <ConfidenceBar confidence={finding.confidence} />
            </div>
          )}
          <p className="text-sm text-[#e5e7eb] mt-1 leading-snug">
            {finding.title}
          </p>
          {finding.severity && (
            <p className="text-xs text-[#6b7280] mt-0.5">
              Severity: {finding.severity}
            </p>
          )}
        </div>
        <span className="text-[#4b5563] text-xs mt-0.5 shrink-0">
          {new Date(finding.modified).toLocaleDateString()}
        </span>
        <span className="text-[#4b5563] text-sm shrink-0">
          {expanded ? "▲" : "▼"}
        </span>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-white/10 px-4 py-3 space-y-3">
          {loadingDetail && (
            <p className="text-xs text-[#4b5563]">Loading...</p>
          )}
          {detail && (
            <pre className="text-xs text-[#9ca3af] whitespace-pre-wrap font-mono leading-relaxed max-h-64 overflow-auto bg-[#13111c] rounded p-3">
              {detail.content}
            </pre>
          )}

          {/* Flag as wrong */}
          {!showCorrect && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowCorrect(true);
              }}
              className="text-xs px-3 py-1.5 rounded bg-white/5 text-[#f59e0b] hover:bg-white/10 border border-[#f59e0b]/20 transition"
            >
              Flag as Wrong
            </button>
          )}
          {showCorrect && (
            <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
              <textarea
                placeholder="Describe what is wrong and what the correct interpretation is..."
                value={correction}
                onChange={(e) => setCorrection(e.target.value)}
                rows={3}
                className="w-full bg-[#13111c] border border-white/10 rounded px-3 py-2 text-xs text-[#e5e7eb] placeholder-[#4b5563] focus:outline-none focus:border-[#f59e0b]/50 resize-none"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setShowCorrect(false);
                    setCorrection("");
                  }}
                  className="text-xs px-3 py-1.5 rounded bg-white/5 text-[#9ca3af] hover:bg-white/10 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={submitCorrection}
                  disabled={submitting || !correction.trim()}
                  className="text-xs px-3 py-1.5 rounded bg-[#f59e0b] text-[#0f0d1a] font-medium hover:brightness-110 disabled:opacity-50 transition"
                >
                  {submitting ? "Saving..." : "Submit Correction"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

type ConfidenceBand = "ALL" | "HIGH" | "MEDIUM" | "LOW";

function getConfidenceBand(confidence: number | null | undefined): "HIGH" | "MEDIUM" | "LOW" | null {
  if (confidence == null) return null;
  if (confidence >= 0.7) return "HIGH";
  if (confidence >= 0.35) return "MEDIUM";
  return "LOW";
}

function ConfidenceBar({ confidence }: { confidence: number | null | undefined }) {
  if (confidence == null) return null;
  const band = getConfidenceBand(confidence);
  const fillColor =
    band === "HIGH" ? "#34d399" : band === "MEDIUM" ? "#f59e0b" : "#ef4444";
  const pct = Math.max(0, Math.min(1, confidence)) * 100;
  return (
    <div className="flex items-center gap-1.5">
      <div className="relative w-[60px] h-[4px] rounded-full bg-white/10 overflow-hidden">
        <div
          className="absolute left-0 top-0 h-full rounded-full"
          style={{ width: `${pct}%`, backgroundColor: fillColor }}
        />
      </div>
      <span className="text-xs font-mono" style={{ color: fillColor }}>
        {confidence.toFixed(2)}
      </span>
    </div>
  );
}

export function FindingFeed({ findings, onRefresh }: Props) {
  const [filterVerdict, setFilterVerdict] = useState("ALL");
  const [filterConfidence, setFilterConfidence] = useState<ConfidenceBand>("ALL");

  const filtered = findings.filter((f) => {
    if (filterVerdict !== "ALL" && f.verdict !== filterVerdict) return false;
    if (filterConfidence !== "ALL") {
      const band = getConfidenceBand(f.confidence);
      if (band !== filterConfidence) return false;
    }
    return true;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <h2 className="text-sm font-semibold text-[#e5e7eb] uppercase tracking-wide">
          Findings ({filtered.length}/{findings.length})
        </h2>
        <div className="flex gap-2">
          <select
            value={filterConfidence}
            onChange={(e) => setFilterConfidence(e.target.value as ConfidenceBand)}
            className="bg-[#1e1b2e] border border-white/10 rounded px-2 py-1 text-xs text-[#9ca3af] focus:outline-none"
          >
            <option value="ALL">All Confidence</option>
            <option value="HIGH">High (≥0.7)</option>
            <option value="MEDIUM">Medium (0.35–0.69)</option>
            <option value="LOW">Low (&lt;0.35)</option>
          </select>
          <select
            value={filterVerdict}
            onChange={(e) => setFilterVerdict(e.target.value)}
            className="bg-[#1e1b2e] border border-white/10 rounded px-2 py-1 text-xs text-[#9ca3af] focus:outline-none"
          >
            <option value="ALL">All Verdicts</option>
            <option value="FAILURE">FAILURE</option>
            <option value="WARNING">WARNING</option>
            <option value="HEALTHY">HEALTHY</option>
            <option value="INCONCLUSIVE">INCONCLUSIVE</option>
          </select>
        </div>
      </div>

      {/* Cards */}
      <div className="flex-1 overflow-auto px-4 py-3 space-y-2">
        {filtered.map((f) => (
          <FindingCard key={f.id} finding={f} onCorrect={onRefresh} />
        ))}
        {filtered.length === 0 && (
          <div className="text-center text-[#4b5563] text-sm py-12">
            No findings match filter
          </div>
        )}
      </div>
    </div>
  );
}
