"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Search, ArrowDown, CheckCircle2, XCircle, Zap, Coins,
  Layers, Filter, Target, Sparkles, Brain, Loader2, Maximize2
} from "lucide-react";
import { searchDocuments, SearchResponse, ScoredChunk } from "@/lib/api";

export default function DashboardPage() {
  return (
    <Suspense fallback={null}>
      <DashboardContent />
    </Suspense>
  );
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState("");
  const [visibleStages, setVisibleStages] = useState(0);
  const resultsRef = useRef<HTMLDivElement>(null);
  const hasAutoRun = useRef(false);

  const runSearch = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    setVisibleStages(0);
    try {
      const res = await searchDocuments({ question: q.trim() });
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  };

  const handleSearch = () => runSearch(question);

  useEffect(() => {
    const q = searchParams.get("q");
    if (q && !hasAutoRun.current) {
      hasAutoRun.current = true;
      setQuestion(q);
      runSearch(q);
    }
  }, [searchParams]);

  useEffect(() => {
    if (!result || loading) return;
    let current = 0;
    const interval = setInterval(() => {
      current++;
      setVisibleStages(current);
      if (current >= 7) clearInterval(interval);
    }, 200);
    return () => clearInterval(interval);
  }, [result, loading]);

  return (
    <div className="pt-24 pb-16">
      <div className="max-w-4xl mx-auto px-6">
        <div className="text-center mb-10 animate-enter">
          <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-5">
            <Brain className="w-7 h-7 text-primary" />
          </div>
          <h1 className="text-3xl font-bold mb-2">Pipeline Visualizer</h1>
          <p className="text-muted-foreground max-w-md mx-auto">
            Watch each stage of the ContextForge optimization pipeline in real-time.
          </p>
        </div>

        <div className="relative mb-12 animate-enter animate-enter-delay-1">
          <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-card border border-border/50 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/10 transition-all">
            <Search className="w-5 h-5 text-muted-foreground ml-4 shrink-0" />
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Ask a question to see the pipeline in action..."
              className="flex-1 py-3 bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none text-sm"
            />
            <button
              onClick={handleSearch}
              disabled={loading || !question.trim()}
              className="px-5 py-2.5 bg-primary text-primary-foreground rounded-xl font-medium text-sm hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2 transition-all shrink-0"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              {loading ? "Running..." : "Run Pipeline"}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm mb-8 animate-enter">
            {error}
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center py-20 gap-6 animate-enter">
            <div className="relative">
              <div className="w-20 h-20 rounded-2xl bg-primary/10 animate-pulse" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-10 h-10 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              </div>
            </div>
            <div className="text-center">
              <p className="font-medium mb-1">Optimizing context</p>
              <p className="text-sm text-muted-foreground">Retrieving, deduplicating, scoring, selecting...</p>
            </div>
          </div>
        )}

        {result && !loading && (
          <div ref={resultsRef} className="space-y-4">
            <Stage visible={visibleStages >= 1}>
              <StageCard icon={<Search className="w-5 h-5" />} title="Question" accent="border-primary/40" iconBg="bg-primary/10" iconColor="text-primary">
                <p className="text-lg font-medium">{result.query}</p>
              </StageCard>
            </Stage>
            <Connector visible={visibleStages >= 2} />
            <Stage visible={visibleStages >= 2}>
              <StageCard icon={<Layers className="w-5 h-5" />} title="Retrieved Chunks" subtitle={`${result.stages.retrieved} chunks from vector search`} accent="border-violet-500/40" iconBg="bg-violet-500/10" iconColor="text-violet-400">
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {result.retrieved.map((c, i) => <ChunkBadge key={i} text={c.text} score={c.score} color="violet" />)}
                </div>
              </StageCard>
            </Stage>
            <Connector visible={visibleStages >= 3} />
            <Stage visible={visibleStages >= 3}>
              <StageCard icon={<Filter className="w-5 h-5" />} title="Deduplication" subtitle={`Threshold: ${result.dedup.threshold} · ${result.dedup.kept_count} kept · ${result.dedup.removed_count} removed`} accent="border-red-500/40" iconBg="bg-red-500/10" iconColor="text-red-400">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5" /> Kept ({result.dedup.kept_count})</p>
                    <div className="space-y-1 max-h-40 overflow-y-auto">
                      {result.dedup.kept.map((c, i) => <ChunkBadge key={i} text={c.text} score={c.score} color="emerald" compact />)}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-2 flex items-center gap-1.5"><XCircle className="w-3.5 h-3.5" /> Removed ({result.dedup.removed_count})</p>
                    <div className="space-y-1 max-h-40 overflow-y-auto">
                      {result.dedup.removed.map((c, i) => <ChunkBadge key={i} text={c.text} score={c.score} color="red" compact />)}
                    </div>
                  </div>
                </div>
              </StageCard>
            </Stage>
            <Connector visible={visibleStages >= 4} />
            <Stage visible={visibleStages >= 4}>
              <StageCard icon={<Target className="w-5 h-5" />} title="Context Scoring" subtitle={`${result.stages.after_scoring} chunks ranked by composite score`} accent="border-amber-500/40" iconBg="bg-amber-500/10" iconColor="text-amber-400">
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {result.scored.map((c, i) => <ScoredRow key={i} chunk={c} rank={i + 1} />)}
                </div>
              </StageCard>
            </Stage>
            <Connector visible={visibleStages >= 5} />
            <Stage visible={visibleStages >= 5}>
              <StageCard icon={<Maximize2 className="w-5 h-5" />} title="Selection" subtitle={`${result.selection.selected_count} chunks · ${result.selection.total_tokens} / ${result.selection.max_budget} tokens`} accent="border-emerald-500/40" iconBg="bg-emerald-500/10" iconColor="text-emerald-400">
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {result.selection.selected.map((c, i) => <ChunkBadge key={i} text={c.text} score={c.context_score} color="emerald" />)}
                </div>
              </StageCard>
            </Stage>
            <Connector visible={visibleStages >= 6} />
            <Stage visible={visibleStages >= 6}>
              <StageCard icon={<Coins className="w-5 h-5" />} title="Token Savings" accent="border-teal-500/40" iconBg="bg-teal-500/10" iconColor="text-teal-400">
                <div className="grid grid-cols-3 gap-3">
                  <SavingsStat value={result.token_summary.tokens_used.toLocaleString()} label="Used" />
                  <SavingsStat value={result.token_summary.tokens_saved.toLocaleString()} label="Saved" color="emerald" />
                  <SavingsStat value={`${result.token_summary.savings_percent}%`} label="Savings" color="amber" />
                </div>
              </StageCard>
            </Stage>
            <Connector visible={visibleStages >= 7} />
            <Stage visible={visibleStages >= 7}>
              <StageCard icon={<Sparkles className="w-5 h-5" />} title="Final Answer" subtitle={`${result.llm_usage.model} · ${result.llm_usage.latency_ms}ms · ${result.llm_usage.total_tokens} tokens`} accent="border-primary/60" iconBg="bg-primary/15" iconColor="text-primary" highlighted>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{result.answer}</p>
              </StageCard>
            </Stage>
          </div>
        )}

        {!result && !loading && !error && (
          <div className="text-center py-16 animate-enter animate-enter-delay-2">
            <div className="w-20 h-20 rounded-2xl bg-accent flex items-center justify-center mx-auto mb-5">
              <Brain className="w-10 h-10 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground">Enter a question above to visualize the pipeline.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function Stage({ visible, children }: { visible: boolean; children: React.ReactNode }) {
  return <div className={`transition-all duration-500 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>{children}</div>;
}

function Connector({ visible }: { visible: boolean }) {
  return <div className={`flex justify-center py-1 transition-all duration-500 ${visible ? "opacity-100" : "opacity-0"}`}><div className="w-0.5 h-6 bg-gradient-to-b from-border to-transparent" /></div>;
}

function StageCard({ icon, title, subtitle, accent, iconBg, iconColor, highlighted, children }: any) {
  return <div className={`rounded-2xl bg-card border ${accent} p-5 transition-all ${highlighted ? "ring-1 ring-primary/20 shadow-lg shadow-primary/5" : "border-border/50"}`}><div className="flex items-center gap-3 mb-4"><div className={`w-10 h-10 rounded-xl ${iconBg} flex items-center justify-center ${iconColor}`}>{icon}</div><div><h3 className="font-semibold text-sm">{title}</h3>{subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}</div></div>{children}</div>;
}

function ChunkBadge({ text, score, color = "violet", compact }: any) {
  const c: any = { violet: "border-violet-500/20 bg-violet-500/5", emerald: "border-emerald-500/20 bg-emerald-500/5", red: "border-red-500/20 bg-red-500/5" };
  return <div className={`p-2.5 rounded-lg border text-xs ${c[color] || c.violet}`}><span className="text-muted-foreground font-mono mr-2">[{score.toFixed(3)}]</span><span className="truncate">{compact ? text.slice(0, 50) + "..." : text.slice(0, 130) + "..."}</span></div>;
}

function ScoredRow({ chunk, rank }: { chunk: ScoredChunk; rank: number }) {
  return <div className="flex items-center gap-3 p-3 rounded-xl bg-accent/30 border border-border/30 text-xs"><span className="w-6 h-6 rounded-lg bg-primary/10 text-primary font-bold flex items-center justify-center text-[11px] shrink-0">{rank}</span><span className="flex-1 truncate">{chunk.text.slice(0, 100)}...</span><span className="font-bold text-primary text-sm shrink-0">{chunk.context_score.toFixed(3)}</span><div className="hidden sm:flex gap-3 text-[10px] text-muted-foreground shrink-0"><FactorBadge label="Sem" value={chunk.semantic_similarity} /><FactorBadge label="Fresh" value={chunk.freshness_score} /><FactorBadge label="Auth" value={chunk.authority_score} /><FactorBadge label="Dens" value={chunk.density_score} /></div></div>;
}

function FactorBadge({ label, value }: { label: string; value: number }) {
  return <div className="text-center"><div className="text-[9px] uppercase opacity-60">{label}</div><div className="font-mono">{value.toFixed(2)}</div></div>;
}

function SavingsStat({ value, label, color = "foreground" }: { value: string; label: string; color?: string }) {
  const cm: any = { emerald: "text-emerald-400", amber: "text-amber-400", foreground: "text-foreground" };
  return <div className="text-center p-3 rounded-xl bg-accent/50"><p className={`text-xl font-bold ${cm[color]}`}>{value}</p><p className="text-xs text-muted-foreground mt-1">{label}</p></div>;
}