"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requireSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { firstZodError, formDataObject, settingsSchema } from "@/lib/validation";

export async function updateSettingsAction(formData: FormData) {
  const session = await requireSession();
  const parsed = settingsSchema.safeParse(formDataObject(formData));
  if (!parsed.success) redirect(`/settings?error=${encodeURIComponent(firstZodError(parsed.error))}`);
  await prisma.$transaction([
    prisma.company.update({ where: { id: session.companyId }, data: { name: parsed.data.companyName, address: parsed.data.companyAddress } }),
    prisma.settings.upsert({
      where: { companyId: session.companyId },
      update: { currency: "EUR", defaultPayrollFrequency: parsed.data.defaultPayrollFrequency },
      create: { companyId: session.companyId, currency: "EUR", defaultPayrollFrequency: parsed.data.defaultPayrollFrequency },
    }),
  ]);
  revalidatePath("/");
  revalidatePath("/settings");
  redirect("/settings?success=Settings+saved.");
}
