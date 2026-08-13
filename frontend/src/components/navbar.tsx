"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, Upload, BarChart3, Command, FileText } from "lucide-react";

const links = [
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/documents", label: "Docs", icon: FileText },
  { href: "/search", label: "Search", icon: Search },
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-16 flex items-center justify-between px-6 border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <Link href="/" className="flex items-center gap-2.5 font-bold text-lg group">
        <div className="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center group-hover:bg-primary/25 transition-colors">
          <Command className="w-4 h-4 text-primary" />
        </div>
        <span className="tracking-tight">
          Context<span className="text-primary">Forge</span>
        </span>
      </Link>

      <div className="flex items-center gap-1">
        {links.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}