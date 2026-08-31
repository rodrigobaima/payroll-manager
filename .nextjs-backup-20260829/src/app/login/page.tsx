import { Building2, LockKeyhole } from "lucide-react";
import { loginAction } from "@/app/actions/auth";
import { FlashMessage } from "@/components/flash-message";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const metadata = { title: "Sign in" };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  return <main className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_top_left,var(--accent),transparent_42%)] p-4"><div className="w-full max-w-md"><div className="mb-6 flex items-center justify-center gap-3"><div className="grid size-11 place-items-center rounded-xl bg-primary text-primary-foreground"><Building2 className="size-5" /></div><div><p className="font-semibold">Payroll Manager</p><p className="text-xs text-muted-foreground">Secure internal access</p></div></div><Card className="shadow-xl shadow-slate-900/5"><CardHeader><CardTitle>Welcome back</CardTitle><CardDescription>Sign in to manage payroll and payslips.</CardDescription></CardHeader><CardContent><FlashMessage error={error} /><form action={loginAction} className="grid gap-4"><div className="form-field"><Label htmlFor="email">Email</Label><Input id="email" name="email" type="email" autoComplete="email" required /></div><div className="form-field"><Label htmlFor="password">Password</Label><Input id="password" name="password" type="password" autoComplete="current-password" required /></div><Button type="submit" size="lg" className="mt-2 w-full"><LockKeyhole />Sign in securely</Button></form></CardContent></Card></div></main>;
}
