"use client";

import { useState } from "react";
import { Search, Loader2, ArrowRight, Sparkles, Zap, Coins, Layers } from "lucide-react";
import { searchDocuments, SearchResponse } from "@/lib/api";
import Link from "next/link";

export default function SearchPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await searchDocuments({ question: question.trim() });
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  };

  return (
    <div className="pt-24 pb-16">
      <div className="max-w-3xl mx-auto px-6">
        <div className="text-center mb-10 animate-enter">
          <h1 className="text-3xl font-bold mb-2">Ask a Question</h1>
          <p className="text-muted-foreground">Get answers backed by optimized context.</p>
        </div>

        <div className="relative mb-8 animate-enter animate-enter-delay-1">
          <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-card border border-border/50 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/10 transition-all">
            <Search className="w-5 h-5 text-muted-foreground ml-4 shrink-0" />
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="What would you like to know about your documents?"
              className="flex-1 py-3 bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none text-sm"
            />
            <button
              onClick={handleSearch}
              disabled={loading || !question.trim()}
              className="px-5 py-2.5 bg-primary text-primary-foreground rounded-xl font-medium text-sm hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2 transition-all shrink-0"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
              {loading ? "Searching" : "Search"}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm mb-6 animate-enter">
            {error}
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center py-16 gap-4 animate-enter">
            <div className="flex gap-1.5">
              {[0, 1, 2].map((i) => (
                <div key={i} className="w-3 h-3 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
            <p className="text-sm text-muted-foreground">Optimizing context...</p>
          </div>
        )}

        {result && !loading && (
          <div className="space-y-5 animate-enter">
            {/* Answer */}
            <div className="p-6 rounded-2xl bg-card border border-primary/20 ring-1 ring-primary/10">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-5 h-5 text-primary" />
                <h3 className="font-semibold">Answer</h3>
              </div>
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{result.answer}</p>
              <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border/50 text-xs text-muted-foreground">
                <span>Model: {result.llm_usage.model}</span>
                <span>Latency: {result.llm_usage.latency_ms}ms</span>
                <span>Tokens: {result.llm_usage.total_tokens}</span>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { icon: Layers, label: "Chunks Used", value: result.stages.after_selection, color: "text-violet-400" },
                { icon: Coins, label: "Tokens Saved", value: result.token_summary.tokens_saved, color: "text-emerald-400" },
                { icon: Zap, label: "Savings", value: `${result.token_summary.savings_percent}%`, color: "text-amber-400" },
              ].map(({ icon: Icon, label, value, color }) => (
                <div key={label} className="p-4 rounded-xl bg-card border border-border/50 text-center">
                  <Icon className={`w-5 h-5 ${color} mx-auto mb-2`} />
                  <p className={`text-xl font-bold ${color}`}>{value}</p>
                  <p className="text-xs text-muted-foreground mt-1">{label}</p>
                </div>
              ))}
            </div>

            {/* Pipeline mini */}
            <div className="p-5 rounded-2xl bg-card border border-border/50">
              <h3 className="text-sm font-semibold mb-3">Pipeline flow</h3>
              <div className="flex items-center gap-2 text-xs flex-wrap">
                {[
                  { label: "Retrieved", count: result.stages.retrieved, color: "bg-violet-500/10 text-violet-400 border-violet-500/20" },
                  { label: "Deduped", count: result.stages.after_dedup, color: "bg-red-500/10 text-red-400 border-red-500/20" },
                  { label: "Scored", count: result.stages.after_scoring, color: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
                  { label: "Selected", count: result.stages.after_selection, color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
                ].map((s, i) => (
                  <span key={i} className="flex items-center gap-2">
                    <span className={`px-3 py-1.5 rounded-full border ${s.color} font-medium`}>{s.label}: {s.count}</span>
                    {i < 3 && <ArrowRight className="w-3 h-3 text-muted-foreground" />}
                  </span>
                ))}
              </div>
            </div>

            <Link
              href={`/dashboard?q=${encodeURIComponent(result.query)}`}
              className="block text-center py-3 rounded-xl bg-accent/50 border border-border/50 text-sm font-medium hover:bg-accent transition-colors"
            >
              View detailed pipeline visualization →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}