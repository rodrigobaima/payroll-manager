"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requireSession } from "@/lib/auth";
import { parseDateInput } from "@/lib/dates";
import { prisma } from "@/lib/prisma";
import { firstZodError, formDataObject, projectSchema } from "@/lib/validation";

function parseProject(formData: FormData) {
  return projectSchema.safeParse({ ...formDataObject(formData), employeeIds: formData.getAll("employeeIds") });
}

export async function createProjectAction(formData: FormData) {
  const session = await requireSession();
  const parsed = parseProject(formData);
  if (!parsed.success) redirect(`/projects/new?error=${encodeURIComponent(firstZodError(parsed.error))}`);
  const validEmployees = await prisma.employee.findMany({ where: { companyId: session.companyId, id: { in: parsed.data.employeeIds } }, select: { id: true } });
  await prisma.project.create({ data: {
    companyId: session.companyId,
    name: parsed.data.name,
    client: parsed.data.client,
    location: parsed.data.location,
    startDate: parseDateInput(parsed.data.startDate),
    status: parsed.data.status,
    notes: parsed.data.notes ?? null,
    employeeLinks: { create: validEmployees.map((employee) => ({ employeeId: employee.id })) },
  } });
  revalidatePath("/projects");
  redirect("/projects?success=Project+created.");
}

export async function updateProjectAction(id: string, formData: FormData) {
  const session = await requireSession();
  const parsed = parseProject(formData);
  if (!parsed.success) redirect(`/projects/${id}/edit?error=${encodeURIComponent(firstZodError(parsed.error))}`);
  const project = await prisma.project.findFirst({ where: { id, companyId: session.companyId } });
  if (!project) redirect("/projects?error=Project+not+found.");
  const validEmployees = await prisma.employee.findMany({ where: { companyId: session.companyId, id: { in: parsed.data.employeeIds } }, select: { id: true } });
  await prisma.$transaction(async (tx) => {
    await tx.projectEmployee.deleteMany({ where: { projectId: id } });
    await tx.project.update({ where: { id }, data: {
      name: parsed.data.name,
      client: parsed.data.client,
      location: parsed.data.location,
      startDate: parseDateInput(parsed.data.startDate),
      status: parsed.data.status,
      notes: parsed.data.notes ?? null,
      employeeLinks: { create: validEmployees.map((employee) => ({ employeeId: employee.id })) },
    } });
  });
  revalidatePath("/projects");
  redirect("/projects?success=Project+updated.");
}

export async function completeProjectAction(id: string) {
  const session = await requireSession();
  await prisma.project.updateMany({ where: { id, companyId: session.companyId }, data: { status: "COMPLETED" } });
  revalidatePath("/projects");
  redirect("/projects?success=Project+completed.");
}
