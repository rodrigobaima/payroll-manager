import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function StatusBadge({ status }: { status: string }) {
  const tone = status === "ACTIVE" || status === "FINALISED" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : status === "REVIEWED" ? "bg-blue-50 text-blue-700 border-blue-200" : status === "DRAFT" ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-slate-50 text-slate-600 border-slate-200";
  return <Badge variant="outline" className={cn("font-medium", tone)}>{status.charAt(0) + status.slice(1).toLowerCase()}</Badge>;
}
