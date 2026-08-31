"use server";

import { Prisma } from "@prisma/client";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requireSession } from "@/lib/auth";
import { parseDateInput } from "@/lib/dates";
import { prisma } from "@/lib/prisma";
import { firstZodError, formDataObject, timesheetSchema } from "@/lib/validation";

export async function createTimesheetAction(formData: FormData) {
  const session = await requireSession();
  const parsed = timesheetSchema.safeParse(formDataObject(formData));
  if (!parsed.success) redirect(`/timesheets?error=${encodeURIComponent(firstZodError(parsed.error))}`);
  const date = parseDateInput(parsed.data.date);
  const [employee, project, daily] = await Promise.all([
    prisma.employee.findFirst({ where: { id: parsed.data.employeeId, companyId: session.companyId, status: "ACTIVE" } }),
    prisma.project.findFirst({ where: { id: parsed.data.projectId, companyId: session.companyId, status: "ACTIVE" } }),
    prisma.timesheetEntry.aggregate({ where: { employeeId: parsed.data.employeeId, date }, _sum: { hours: true } }),
  ]);
  if (!employee || !project) redirect("/timesheets?error=Select+an+active+employee+and+project.");
  const total = Number(daily._sum.hours ?? 0) + parsed.data.hours;
  if (total > 24) redirect("/timesheets?error=Daily+hours+cannot+exceed+24.");
  try {
    await prisma.timesheetEntry.create({ data: { employeeId: employee.id, projectId: project.id, date, hours: parsed.data.hours.toFixed(2) } });
    await prisma.projectEmployee.upsert({
      where: { projectId_employeeId: { projectId: project.id, employeeId: employee.id } },
      update: {},
      create: { projectId: project.id, employeeId: employee.id },
    });
  } catch (error) {
    const message = error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2002"
      ? "An entry already exists for that employee, project and date."
      : "The timesheet entry could not be saved.";
    redirect(`/timesheets?error=${encodeURIComponent(message)}`);
  }
  revalidatePath("/timesheets");
  redirect("/timesheets?success=Timesheet+entry+added.");
}

export async function deleteTimesheetAction(id: string) {
  const session = await requireSession();
  const entry = await prisma.timesheetEntry.findFirst({ where: { id, employee: { companyId: session.companyId } } });
  if (entry) await prisma.timesheetEntry.delete({ where: { id } });
  revalidatePath("/timesheets");
  redirect("/timesheets?success=Timesheet+entry+removed.");
}
