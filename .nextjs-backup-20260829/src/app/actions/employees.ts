"use server";

import { Prisma } from "@prisma/client";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requireSession } from "@/lib/auth";
import { parseDateInput } from "@/lib/dates";
import { prisma } from "@/lib/prisma";
import { employeeSchema, firstZodError, formDataObject } from "@/lib/validation";

function employeeData(data: ReturnType<typeof employeeSchema.parse>) {
  return {
    fullName: data.fullName,
    employeeId: data.employeeId,
    email: data.email.toLowerCase(),
    phone: data.phone ?? null,
    paymentType: data.paymentType,
    hourlyRate: data.paymentType === "HOURLY" ? data.hourlyRate! : null,
    monthlySalary: data.paymentType === "MONTHLY" ? data.monthlySalary! : null,
    startDate: parseDateInput(data.startDate),
    status: data.status,
  };
}

export async function createEmployeeAction(formData: FormData) {
  const session = await requireSession();
  const parsed = employeeSchema.safeParse(formDataObject(formData));
  if (!parsed.success) redirect(`/employees/new?error=${encodeURIComponent(firstZodError(parsed.error))}`);
  try {
    await prisma.employee.create({ data: { companyId: session.companyId, ...employeeData(parsed.data) } });
  } catch (error) {
    const message = error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2002"
      ? "Employee ID or email is already in use."
      : "The employee could not be saved.";
    redirect(`/employees/new?error=${encodeURIComponent(message)}`);
  }
  revalidatePath("/employees");
  redirect("/employees?success=Employee+created.");
}

export async function updateEmployeeAction(id: string, formData: FormData) {
  const session = await requireSession();
  const parsed = employeeSchema.safeParse(formDataObject(formData));
  if (!parsed.success) redirect(`/employees/${id}/edit?error=${encodeURIComponent(firstZodError(parsed.error))}`);
  const existing = await prisma.employee.findFirst({ where: { id, companyId: session.companyId } });
  if (!existing) redirect("/employees?error=Employee+not+found.");
  try {
    await prisma.employee.update({ where: { id }, data: employeeData(parsed.data) });
  } catch (error) {
    const message = error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2002"
      ? "Employee ID or email is already in use."
      : "The employee could not be updated.";
    redirect(`/employees/${id}/edit?error=${encodeURIComponent(message)}`);
  }
  revalidatePath("/employees");
  redirect("/employees?success=Employee+updated.");
}

export async function deactivateEmployeeAction(id: string) {
  const session = await requireSession();
  await prisma.employee.updateMany({ where: { id, companyId: session.companyId }, data: { status: "INACTIVE" } });
  revalidatePath("/employees");
  redirect("/employees?success=Employee+marked+inactive.");
}
