import { AlertCircle, CheckCircle2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export function FlashMessage({ success, error }: { success?: string; error?: string }) {
  const message = error ?? success;
  if (!message) return null;
  const Icon = error ? AlertCircle : CheckCircle2;
  return <Alert variant={error ? "destructive" : "default"} className="mb-6 bg-card"><Icon /><AlertDescription>{message}</AlertDescription></Alert>;
}
