"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart, Home, Layers, Library, Play, Settings } from "lucide-react";
import { AuthGuard } from "@/components/AuthGuard";
import { useLogout } from "@/hooks/useAuth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/study", label: "Study", icon: Play },
  { href: "/library", label: "Library", icon: Library },
  { href: "/decks", label: "Decks", icon: Layers },
  { href: "/stats", label: "Stats", icon: BarChart },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const logout = useLogout();

  return (
    <AuthGuard>
      <div className="grid grid-cols-[220px_1fr] min-h-screen">
        <aside className="bg-slate-900 text-slate-200 p-4 flex flex-col">
          <div className="text-xl font-bold text-white mb-6">📚 Tlearning</div>
          <nav className="flex-1 space-y-1">
            {NAV.map(({ href, label, icon: Icon }) => {
              const active = pathname?.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-2 px-3 py-2 rounded text-sm ${
                    active
                      ? "bg-indigo-600 text-white"
                      : "hover:bg-slate-800"
                  }`}
                >
                  <Icon size={16} /> {label}
                </Link>
              );
            })}
          </nav>
          <button
            type="button"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
            className="text-xs text-slate-400 hover:text-white text-left disabled:opacity-50"
          >
            {logout.isPending ? "Logging out…" : "Log out"}
          </button>
        </aside>
        <main className="p-6 bg-slate-50">{children}</main>
      </div>
    </AuthGuard>
  );
}
