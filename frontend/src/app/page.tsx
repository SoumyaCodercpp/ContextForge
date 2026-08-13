import Link from "next/link";
import { ArrowRight, Upload, Search, BarChart3, Zap, Shield, Sparkles } from "lucide-react";

export default function Home() {
  return (
    <div className="pt-24 pb-16">
      <div className="max-w-4xl mx-auto px-6">
        {/* Hero */}
        <div className="text-center mb-20 animate-enter">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-sm text-primary mb-8">
            <Sparkles className="w-3.5 h-3.5" />
            Now in public beta
          </div>
          <h1 className="text-5xl sm:text-6xl font-bold tracking-tight leading-tight mb-6">
            Forge the perfect
            <br />
            <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
              LLM context
            </span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-xl mx-auto leading-relaxed mb-10">
            Stop wasting tokens on duplicate and low-quality chunks. ContextForge intelligently 
            deduplicates, scores, and selects only the most valuable context before it reaches your LLM.
          </p>

          <div className="flex items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-semibold hover:bg-primary/90 transition-all hover:shadow-lg hover:shadow-primary/25 flex items-center gap-2"
            >
              Try the pipeline <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/upload"
              className="px-6 py-3 border border-border rounded-xl font-medium hover:bg-accent transition-all"
            >
              Upload documents
            </Link>
          </div>
        </div>

        {/* Stats mini */}
        <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto mb-20 animate-enter animate-enter-delay-1">
          {[
            { value: "3-stage", label: "Pipeline" },
            { value: "~40%", label: "Avg token savings" },
            { value: "< 2s", label: "Processing time" },
          ].map(({ value, label }) => (
            <div key={label} className="text-center p-4 rounded-xl bg-card border border-border/50">
              <p className="text-2xl font-bold text-primary">{value}</p>
              <p className="text-xs text-muted-foreground mt-1">{label}</p>
            </div>
          ))}
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-20">
          {[
            {
              icon: Zap,
              title: "Deduplication",
              desc: "Embedding-based near-duplicate detection removes redundant chunks before they waste tokens.",
            },
            {
              icon: Shield,
              title: "Multi-factor Scoring",
              desc: "Chunks scored on semantic similarity, freshness, authority, and information density.",
            },
            {
              icon: Sparkles,
              title: "Smart Selection",
              desc: "Knapsack-optimized chunk selection maximizes context value within your token budget.",
            },
          ].map(({ icon: Icon, title, desc }, i) => (
            <div
              key={title}
              className={`p-6 rounded-2xl bg-card border border-border/50 hover:border-primary/30 transition-all duration-300 hover:-translate-y-1 animate-enter animate-enter-delay-${i + 2}`}
            >
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                <Icon className="w-5 h-5 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">{title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        {/* Action cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 animate-enter animate-enter-delay-4">
          {[
            { href: "/upload", icon: Upload, title: "Upload", desc: "Index PDF documents" },
            { href: "/search", icon: Search, title: "Search", desc: "Ask questions" },
            { href: "/dashboard", icon: BarChart3, title: "Dashboard", desc: "Visualize pipeline" },
          ].map(({ href, icon: Icon, title, desc }) => (
            <Link
              key={href}
              href={href}
              className="p-5 rounded-2xl bg-card border border-border/50 hover:border-primary/40 transition-all group"
            >
              <Icon className="w-6 h-6 text-primary mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="font-semibold">{title}</h3>
              <p className="text-sm text-muted-foreground">{desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}