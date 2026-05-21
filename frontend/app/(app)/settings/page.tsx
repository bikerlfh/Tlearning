"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";

const SECTIONS = [
  {
    href: "/settings/profile",
    title: "Profile",
    desc: "Name, timezone, UI language",
  },
  {
    href: "/settings/api-tokens",
    title: "API tokens",
    desc: "Bearer tokens for MCP clients",
  },
  {
    href: "/settings/integrations",
    title: "Integrations",
    desc: "Claude Desktop, Cursor, Custom GPT",
  },
  {
    href: "/settings/notifications",
    title: "Notifications",
    desc: "Push prefs and quiet hours",
  },
];

export default function SettingsIndex() {
  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Settings</h1>
      <div className="space-y-3">
        {SECTIONS.map((s) => (
          <Link key={s.href} href={s.href} className="block">
            <Card className="p-4 hover:bg-slate-50 transition">
              <div className="font-bold">{s.title}</div>
              <div className="text-sm text-slate-600">{s.desc}</div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
