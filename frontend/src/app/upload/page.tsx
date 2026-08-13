"use client";

import { useState, useRef } from "react";
import { Upload, FileText, CheckCircle, Loader2, X, File } from "lucide-react";
import { uploadDocuments, UploadResponse } from "@/lib/api";

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async () => {
    if (!files.length) return;
    setUploading(true);
    setError("");
    setResult(null);
    try {
      const res = await uploadDocuments(files);
      setResult(res);
      setFiles([]);
    } catch (e: any) {
      setError(e.message);
    }
    setUploading(false);
  };

  const removeFile = (i: number) => setFiles(files.filter((_, idx) => idx !== i));

  return (
    <div className="pt-24 pb-16">
      <div className="max-w-2xl mx-auto px-6">
        <div className="text-center mb-12 animate-enter">
          <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-5">
            <Upload className="w-7 h-7 text-primary" />
          </div>
          <h1 className="text-3xl font-bold mb-2">Upload Documents</h1>
          <p className="text-muted-foreground">Add PDFs to your knowledge base for indexing.</p>
        </div>

        {/* Drop zone */}
        <div
          className={`relative rounded-2xl border-2 border-dashed p-16 text-center cursor-pointer transition-all duration-200 animate-enter animate-enter-delay-1 ${
            dragOver
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary/50 hover:bg-card"
          }`}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            const dropped = Array.from(e.dataTransfer.files).filter((f) => f.name.endsWith(".pdf"));
            setFiles((prev) => [...prev, ...dropped]);
          }}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onClick={() => inputRef.current?.click()}
        >
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <File className="w-8 h-8 text-primary" />
          </div>
          <p className="font-semibold text-lg mb-1">Drop your PDFs here</p>
          <p className="text-sm text-muted-foreground">or click to browse</p>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              const selected = Array.from(e.target.files || []);
              setFiles((prev) => [...prev, ...selected]);
            }}
          />
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div className="mt-6 animate-enter animate-enter-delay-2">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-medium text-muted-foreground">
                {files.length} file{files.length > 1 ? "s" : ""} selected
              </p>
              <button
                onClick={() => setFiles([])}
                className="text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Clear all
              </button>
            </div>
            <div className="space-y-2 mb-5">
              {files.map((f, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 rounded-xl bg-card border border-border/50"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="w-4 h-4 text-primary" />
                    <span className="text-sm truncate max-w-[300px]">{f.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {(f.size / 1024).toFixed(0)} KB
                    </span>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                    className="p-1 rounded-lg hover:bg-accent transition-colors"
                  >
                    <X className="w-4 h-4 text-muted-foreground" />
                  </button>
                </div>
              ))}
            </div>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="w-full py-3 bg-primary text-primary-foreground rounded-xl font-semibold hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2 transition-all"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Indexing documents...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Upload & Index
                </>
              )}
            </button>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-6 p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm animate-enter">
            {error}
          </div>
        )}

        {/* Success */}
        {result && (
          <div className="mt-6 p-6 rounded-2xl bg-card border border-border/50 animate-enter">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-success/10 flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-success" />
              </div>
              <div>
                <p className="font-semibold">{result.message}</p>
                <p className="text-xs text-muted-foreground">
                  Completed in {result.processing_time_ms}ms
                </p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Documents", value: result.document_ids.length },
                { label: "Total Chunks", value: result.total_chunks },
                { label: "Files", value: result.filenames.length },
              ].map(({ label, value }) => (
                <div key={label} className="p-3 rounded-xl bg-accent/50 text-center">
                  <p className="text-xl font-bold">{value}</p>
                  <p className="text-xs text-muted-foreground mt-1">{label}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}