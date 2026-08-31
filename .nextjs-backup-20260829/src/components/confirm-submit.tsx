"use client";

import { Button } from "@/components/ui/button";

export function ConfirmSubmit({ children, message, variant = "destructive" }: { children: React.ReactNode; message: string; variant?: "destructive" | "outline" | "default" }) {
  return <Button type="submit" variant={variant} onClick={(event) => { if (!window.confirm(message)) event.preventDefault(); }}>{children}</Button>;
}
