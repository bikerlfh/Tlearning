"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart, Home, Layers, Library, Play, Settings } from "lucide-react";
import { AuthGuard } from "@/components/AuthGuard";
import { OnboardingModal } from "@/components/OnboardingModal";
import { useLogout, useMe } from "@/hooks/useAuth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/study", label: "Study", icon: Play },
  { href: "/library", label: "Library", icon: Library },
  { href: "/decks", label: "Decks", icon: Layers },
  { href: "/stats", label: "Stats", icon: BarChart },
  { href: "/settings", label: "Settings", icon: Settings },
];

function OnboardingTrigger() {
  const me = useMe();
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!me.data) return;
    const flag = window.localStorage.getItem("tlearning_onboarded");
    if (!flag) setOpen(true);
  }, [me.data]);
  return <OnboardingModal open={open} onClose={() => setOpen(false)} />;
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const logout = useLogout();

  return (
    <AuthGuard>
      <div className="md:grid md:grid-cols-[220px_1fr] min-h-screen">
        <aside className="hidden md:flex bg-slate-900 text-slate-200 p-4 flex-col">
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
        <main className="p-4 md:p-6 bg-slate-50 pb-20 md:pb-6">{children}</main>
        {/* Mobile bottom tab bar */}
        <nav className="md:hidden fixed bottom-0 inset-x-0 bg-slate-900 text-slate-200 grid grid-cols-6 gap-0 z-20 border-t border-slate-800">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname?.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex flex-col items-center justify-center py-2 text-[10px] ${
                  active ? "text-indigo-300" : "text-slate-400"
                }`}
                aria-label={label}
              >
                <Icon size={20} />
                <span className="mt-0.5">{label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
      <OnboardingTrigger />
    </AuthGuard>
  );
}
