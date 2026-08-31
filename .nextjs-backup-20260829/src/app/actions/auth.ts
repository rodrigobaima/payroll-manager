"use server";

import { compare } from "bcryptjs";
import { redirect } from "next/navigation";
import { z } from "zod";
import { clearSession, createSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

const loginSchema = z.object({ email: z.email(), password: z.string().min(1) });

export async function loginAction(formData: FormData) {
  const parsed = loginSchema.safeParse(Object.fromEntries(formData.entries()));
  if (!parsed.success) redirect("/login?error=Enter+a+valid+email+and+password.");

  const user = await prisma.user.findUnique({ where: { email: parsed.data.email.toLowerCase() } });
  if (!user || !(await compare(parsed.data.password, user.passwordHash))) {
    redirect("/login?error=Invalid+email+or+password.");
  }
  await createSession({ userId: user.id, companyId: user.companyId, email: user.email, name: user.name });
  redirect("/");
}

export async function logoutAction() {
  await clearSession();
  redirect("/login");
}
