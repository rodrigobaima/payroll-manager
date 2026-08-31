import { Sidebar } from "@/components/shell/sidebar";
import { requireSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await requireSession();
  const company = await prisma.company.findUnique({ where: { id: session.companyId }, select: { name: true } });
  return <div className="min-h-screen lg:flex"><Sidebar companyName={company?.name ?? "Engineering Office"} userName={session.name} /><main className="min-w-0 flex-1"><div className="page-shell">{children}</div></main></div>;
}
