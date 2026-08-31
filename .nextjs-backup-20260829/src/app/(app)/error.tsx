"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <div className="rounded-xl border bg-card p-8 text-center"><AlertTriangle className="mx-auto mb-3 size-8 text-destructive" /><h2 className="text-lg font-semibold">We could not load this page</h2><p className="mt-1 text-sm text-muted-foreground">Check the database connection and try again. No payroll data was changed.</p><Button className="mt-4" onClick={reset}>Try again</Button></div>;
}
