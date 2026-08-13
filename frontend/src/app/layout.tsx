import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Navbar } from "@/components/navbar";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ContextForge — Intelligent Context Optimization",
  description: "Optimize your RAG pipeline context. Deduplicate, score, and select the best chunks before they reach your LLM.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen bg-background text-foreground`}>
        <Navbar />
        {children}
      </body>
    </html>
  );
}