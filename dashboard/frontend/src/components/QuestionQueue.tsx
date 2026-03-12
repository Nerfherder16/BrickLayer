import { useState } from "react";
import { api, Question } from "../lib/api";

interface Props {
  questions: Question[];
  onRefresh: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  PENDING: "bg-[#374151] text-[#9ca3af]",
  DONE: "bg-[#064e3b] text-[#34d399]",
  INCONCLUSIVE: "bg-[#451a03] text-[#f59e0b]",
  IN_PROGRESS: "bg-[#1e3a5f] text-[#38bdf8]",
};

const DOMAINS = ["D1", "D2", "D3", "D4", "D5", "D6"];

export function QuestionQueue({ questions, onRefresh }: Props) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    question: "",
    domain: "D1",
    hypothesis: "",
    priority: "end" as "next" | "end",
  });
  const [submitting, setSubmitting] = useState(false);
  const [filterDomain, setFilterDomain] = useState<string>("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  const handleSubmit = async () => {
    if (!form.question.trim()) return;
    setSubmitting(true);
    try {
      await api.addQuestion(form);
      setForm({ question: "", domain: "D1", hypothesis: "", priority: "end" });
      setShowForm(false);
      onRefresh();
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = questions.filter((q) => {
    if (filterDomain !== "ALL" && q.domain !== filterDomain) return false;
    if (filterStatus !== "ALL" && q.status !== filterStatus) return false;
    return true;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <h2 className="text-sm font-semibold text-[#e5e7eb] uppercase tracking-wide">
          Questions ({filtered.length}/{questions.length})
        </h2>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="text-xs px-3 py-1.5 rounded bg-[#38bdf8] text-[#0f0d1a] font-medium hover:brightness-110 transition"
        >
          + Add Question
        </button>
      </div>

      {/* Add Question Form */}
      {showForm && (
        <div className="px-4 py-3 bg-[#252236] border-b border-white/10 space-y-2">
          <div className="flex gap-2">
            <select
              value={form.domain}
              onChange={(e) =>
                setForm((f) => ({ ...f, domain: e.target.value }))
              }
              className="bg-[#1e1b2e] border border-white/10 rounded px-2 py-1.5 text-sm text-[#e5e7eb] focus:outline-none focus:border-[#38bdf8]/50"
            >
              {DOMAINS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            <div className="flex gap-1 items-center">
              <button
                onClick={() => setForm((f) => ({ ...f, priority: "next" }))}
                className={`text-xs px-2 py-1 rounded transition ${form.priority === "next" ? "bg-[#38bdf8] text-[#0f0d1a]" : "bg-white/5 text-[#9ca3af] hover:bg-white/10"}`}
              >
                Next
              </button>
              <button
                onClick={() => setForm((f) => ({ ...f, priority: "end" }))}
                className={`text-xs px-2 py-1 rounded transition ${form.priority === "end" ? "bg-[#38bdf8] text-[#0f0d1a]" : "bg-white/5 text-[#9ca3af] hover:bg-white/10"}`}
              >
                End
              </button>
            </div>
          </div>
          <textarea
            placeholder="Question text..."
            value={form.question}
            onChange={(e) =>
              setForm((f) => ({ ...f, question: e.target.value }))
            }
            rows={2}
            className="w-full bg-[#1e1b2e] border border-white/10 rounded px-3 py-2 text-sm text-[#e5e7eb] placeholder-[#4b5563] focus:outline-none focus:border-[#38bdf8]/50 resize-none"
          />
          <input
            placeholder="Hypothesis (optional)..."
            value={form.hypothesis}
            onChange={(e) =>
              setForm((f) => ({ ...f, hypothesis: e.target.value }))
            }
            className="w-full bg-[#1e1b2e] border border-white/10 rounded px-3 py-2 text-sm text-[#e5e7eb] placeholder-[#4b5563] focus:outline-none focus:border-[#38bdf8]/50"
          />
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowForm(false)}
              className="text-xs px-3 py-1.5 rounded bg-white/5 text-[#9ca3af] hover:bg-white/10 transition"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting || !form.question.trim()}
              className="text-xs px-3 py-1.5 rounded bg-[#38bdf8] text-[#0f0d1a] font-medium hover:brightness-110 disabled:opacity-50 transition"
            >
              {submitting ? "Adding..." : "Add"}
            </button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 px-4 py-2 border-b border-white/5 flex-wrap">
        <select
          value={filterDomain}
          onChange={(e) => setFilterDomain(e.target.value)}
          className="bg-[#1e1b2e] border border-white/10 rounded px-2 py-1 text-xs text-[#9ca3af] focus:outline-none"
        >
          <option value="ALL">All Domains</option>
          {DOMAINS.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="bg-[#1e1b2e] border border-white/10 rounded px-2 py-1 text-xs text-[#9ca3af] focus:outline-none"
        >
          <option value="ALL">All Status</option>
          <option value="PENDING">PENDING</option>
          <option value="DONE">DONE</option>
          <option value="INCONCLUSIVE">INCONCLUSIVE</option>
          <option value="IN_PROGRESS">IN_PROGRESS</option>
        </select>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-[#1e1b2e] border-b border-white/10">
            <tr>
              <th className="text-left px-4 py-2 text-xs uppercase tracking-wide text-[#9ca3af] font-medium w-16">
                ID
              </th>
              <th className="text-left px-2 py-2 text-xs uppercase tracking-wide text-[#9ca3af] font-medium w-10">
                D
              </th>
              <th className="text-left px-2 py-2 text-xs uppercase tracking-wide text-[#9ca3af] font-medium">
                Question
              </th>
              <th className="text-left px-4 py-2 text-xs uppercase tracking-wide text-[#9ca3af] font-medium w-28">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((q, i) => (
              <tr
                key={q.id}
                className={`border-b border-white/5 hover:bg-white/[0.03] transition-colors ${i % 2 === 0 ? "" : ""}`}
              >
                <td className="px-4 py-2 font-mono text-xs text-[#9ca3af]">
                  {q.id}
                </td>
                <td className="px-2 py-2 text-xs text-[#6b7280]">{q.domain}</td>
                <td className="px-2 py-2 text-[#e5e7eb] leading-snug">
                  {q.title}
                </td>
                <td className="px-4 py-2">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[q.status] ?? "bg-[#374151] text-[#9ca3af]"}`}
                  >
                    {q.status}
                  </span>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td
                  colSpan={4}
                  className="px-4 py-8 text-center text-[#4b5563] text-sm"
                >
                  No questions match filters
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
