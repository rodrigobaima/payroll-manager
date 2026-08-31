"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Building2,
  CalendarClock,
  FileText,
  FolderKanban,
  LayoutDashboard,
  LogOut,
  Settings,
  Users,
  WalletCards,
} from "lucide-react";
import { logoutAction } from "@/app/actions/auth";
import { cn } from "@/lib/utils";

const navigation = [
  ["Dashboard", "/", LayoutDashboard],
  ["Projects", "/projects", FolderKanban],
  ["Employees", "/employees", Users],
  ["Timesheets", "/timesheets", CalendarClock],
  ["Payroll", "/payroll", WalletCards],
  ["Payslips", "/payslips", FileText],
  ["Settings", "/settings", Settings],
] as const;

export function Sidebar({ companyName, userName }: { companyName: string; userName: string }) {
  const pathname = usePathname();
  return (
    <aside className="border-sidebar-border bg-sidebar text-sidebar-foreground lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64 lg:flex-col lg:border-r">
      <div className="flex items-center gap-3 border-b border-sidebar-border px-5 py-5">
        <div className="grid size-10 place-items-center rounded-xl bg-sidebar-primary text-sidebar-primary-foreground"><Building2 className="size-5" /></div>
        <div className="min-w-0"><p className="text-xs text-sidebar-foreground/60">Payroll Manager</p><p className="truncate text-sm font-semibold">{companyName}</p></div>
      </div>
      <nav className="flex gap-1 overflow-x-auto p-3 lg:flex-1 lg:flex-col lg:overflow-visible" aria-label="Primary navigation">
        {navigation.map(([label, href, Icon]) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return <Link key={href} href={href} className={cn("flex shrink-0 items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-sidebar-foreground/70 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground", active && "bg-sidebar-accent text-sidebar-accent-foreground")}><Icon className="size-4" />{label}</Link>;
        })}
      </nav>
      <div className="hidden border-t border-sidebar-border p-4 lg:block">
        <p className="truncate text-sm font-medium">{userName}</p>
        <form action={logoutAction} className="mt-2"><button className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"><LogOut className="size-4" />Sign out</button></form>
      </div>
    </aside>
  );
}
