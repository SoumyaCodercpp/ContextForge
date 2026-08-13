"use client";

import { useState, useEffect } from "react";
import { FileText, Search, Clock, Database, Layers, CircleCheck } from "lucide-react";
import { getMetrics, MetricsResponse } from "@/lib/api";

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMetrics()
      .then(setMetrics)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const vectorInfo = metrics?.vector_collection_info as any;

  return (
    <div className="pt-24 pb-16">
      <div className="max-w-3xl mx-auto px-6">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold mb-2">System Metrics</h1>
          <p className="text-muted-foreground">Aggregate pipeline statistics.</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-10">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : metrics ? (
          <div className="space-y-6">
            {/* Main stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-6 rounded-2xl bg-card border border-border/50 text-center">
                <FileText className="w-6 h-6 text-primary mx-auto mb-3" />
                <p className="text-3xl font-bold">{metrics.total_documents}</p>
                <p className="text-sm text-muted-foreground mt-1">Documents</p>
              </div>
              <div className="p-6 rounded-2xl bg-card border border-border/50 text-center">
                <Layers className="w-6 h-6 text-primary mx-auto mb-3" />
                <p className="text-3xl font-bold">{metrics.total_chunks}</p>
                <p className="text-sm text-muted-foreground mt-1">Chunks</p>
              </div>
              <div className="p-6 rounded-2xl bg-card border border-border/50 text-center">
                <Search className="w-6 h-6 text-primary mx-auto mb-3" />
                <p className="text-3xl font-bold">{metrics.total_searches}</p>
                <p className="text-sm text-muted-foreground mt-1">Searches</p>
              </div>
              <div className="p-6 rounded-2xl bg-card border border-border/50 text-center">
                <Clock className="w-6 h-6 text-primary mx-auto mb-3" />
                <p className="text-3xl font-bold">{Math.round(metrics.avg_pipeline_latency_ms)}ms</p>
                <p className="text-sm text-muted-foreground mt-1">Avg Latency</p>
              </div>
            </div>

            {/* Qdrant summary */}
            {vectorInfo && (
              <div className="p-6 rounded-2xl bg-card border border-border/50">
                <h3 className="font-semibold mb-4">Vector Database</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <CircleCheck className="w-4 h-4 text-emerald-400" />
                    <span className="text-muted-foreground">Status:</span>
                    <span className="font-medium">{vectorInfo.status || "unknown"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-primary" />
                    <span className="text-muted-foreground">Points:</span>
                    <span className="font-medium">{vectorInfo.points_count || 0}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">Vector Size:</span>
                    <span className="font-medium">{vectorInfo.config?.params?.vectors?.size || "—"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">Distance:</span>
                    <span className="font-medium">{vectorInfo.config?.params?.vectors?.distance || "—"}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-center text-muted-foreground py-10">Failed to load metrics.</p>
        )}
      </div>
    </div>
  );
}