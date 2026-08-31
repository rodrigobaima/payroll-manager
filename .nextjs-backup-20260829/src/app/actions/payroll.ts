"use server";

import { Prisma } from "@prisma/client";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requireSession } from "@/lib/auth";
import { parseDateInput } from "@/lib/dates";
import { calculateNetPay } from "@/lib/money";
import { assertPayrollEditable, calculateGrossForEmployee } from "@/lib/payroll";
import { prisma } from "@/lib/prisma";
import {
  deductionsSchema,
  firstZodError,
  formDataObject,
  payrollPeriodSchema,
} from "@/lib/validation";

export async function createPayrollAction(formData: FormData) {
  const session = await requireSession();
  const parsed = payrollPeriodSchema.safeParse(formDataObject(formData));
  if (!parsed.success) redirect(`/payroll/new?error=${encodeURIComponent(firstZodError(parsed.error))}`);

  const startDate = parseDateInput(parsed.data.startDate);
  const endDate = parseDateInput(parsed.data.endDate);
  const employees = await prisma.employee.findMany({
    where: { companyId: session.companyId, status: "ACTIVE" },
    orderBy: { fullName: "asc" },
  });
  if (employees.length === 0) redirect("/payroll/new?error=Add+an+active+employee+before+running+payroll.");

  const hours = await prisma.timesheetEntry.groupBy({
    by: ["employeeId"],
    where: { employee: { companyId: session.companyId }, date: { gte: startDate, lte: endDate } },
    _sum: { hours: true },
  });
  const hoursByEmployee = new Map(hours.map((row) => [row.employeeId, row._sum.hours?.toString() ?? "0"]));

  let periodId: string;
  try {
    periodId = await prisma.$transaction(async (tx) => {
      const period = await tx.payrollPeriod.create({ data: {
        companyId: session.companyId,
        frequency: parsed.data.frequency,
        startDate,
        endDate,
        payDate: parseDateInput(parsed.data.payDate),
        status: "DRAFT",
      } });
      for (const employee of employees) {
        const hoursWorked = hoursByEmployee.get(employee.id) ?? "0";
        const gross = calculateGrossForEmployee({
          paymentType: employee.paymentType,
          hoursWorked,
          hourlyRate: employee.hourlyRate?.toString() ?? null,
          monthlySalary: employee.monthlySalary?.toString() ?? null,
        });
        await tx.payrollEntry.create({ data: {
          payrollPeriodId: period.id,
          employeeId: employee.id,
          employeeName: employee.fullName,
          employeeNumber: employee.employeeId,
          paymentType: employee.paymentType,
          hoursWorked,
          hourlyRate: employee.hourlyRate,
          monthlySalary: employee.monthlySalary,
          grossPay: gross.toFixed(2),
          paye: "0.00",
          usc: "0.00",
          prsi: "0.00",
          otherDeductions: "0.00",
          totalDeductions: "0.00",
          netPay: gross.toFixed(2),
        } });
      }
      return period.id;
    });
  } catch (error) {
    const message = error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2002"
      ? "That payroll period already exists."
      : "Payroll could not be created.";
    redirect(`/payroll/new?error=${encodeURIComponent(message)}`);
  }
  revalidatePath("/payroll");
  redirect(`/payroll/${periodId}?success=Draft+payroll+created.`);
}

export async function updateDeductionsAction(periodId: string, formData: FormData) {
  const session = await requireSession();
  const parsed = deductionsSchema.safeParse(formDataObject(formData));
  if (!parsed.success) redirect(`/payroll/${periodId}?error=${encodeURIComponent(firstZodError(parsed.error))}`);
  const entry = await prisma.payrollEntry.findFirst({
    where: { id: parsed.data.payrollEntryId, payrollPeriod: { id: periodId, companyId: session.companyId } },
    include: { payrollPeriod: true },
  });
  if (!entry) redirect(`/payroll/${periodId}?error=Payroll+entry+not+found.`);
  try {
    assertPayrollEditable(entry.payrollPeriod.status);
    const calculated = calculateNetPay(entry.grossPay.toString(), parsed.data);
    await prisma.payrollEntry.update({ where: { id: entry.id }, data: {
      paye: calculated.paye.toFixed(2),
      usc: calculated.usc.toFixed(2),
      prsi: calculated.prsi.toFixed(2),
      otherDeductions: calculated.otherDeductions.toFixed(2),
      totalDeductions: calculated.totalDeductions.toFixed(2),
      netPay: calculated.netPay.toFixed(2),
    } });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Deductions could not be updated.";
    redirect(`/payroll/${periodId}?error=${encodeURIComponent(message)}`);
  }
  revalidatePath(`/payroll/${periodId}`);
  redirect(`/payroll/${periodId}?success=Deductions+updated.`);
}

export async function reviewPayrollAction(periodId: string) {
  const session = await requireSession();
  const updated = await prisma.payrollPeriod.updateMany({
    where: { id: periodId, companyId: session.companyId, status: "DRAFT" },
    data: { status: "REVIEWED", reviewedAt: new Date() },
  });
  if (updated.count === 0) redirect(`/payroll/${periodId}?error=Only+a+draft+payroll+can+be+reviewed.`);
  revalidatePath(`/payroll/${periodId}`);
  redirect(`/payroll/${periodId}?success=Payroll+ready+for+final+review.`);
}

export async function finalisePayrollAction(periodId: string) {
  const session = await requireSession();
  const period = await prisma.payrollPeriod.findFirst({
    where: { id: periodId, companyId: session.companyId },
    include: { entries: true },
  });
  if (!period || period.status !== "REVIEWED") {
    redirect(`/payroll/${periodId}?error=Payroll+must+be+reviewed+before+finalising.`);
  }
  if (period.entries.some((entry) => entry.netPay.isNegative() || entry.totalDeductions.greaterThan(entry.grossPay))) {
    redirect(`/payroll/${periodId}?error=Correct+invalid+deductions+before+finalising.`);
  }
  const updated = await prisma.payrollPeriod.updateMany({
    where: { id: periodId, companyId: session.companyId, status: "REVIEWED" },
    data: { status: "FINALISED", finalisedAt: new Date() },
  });
  if (updated.count === 0) redirect(`/payroll/${periodId}?error=Payroll+state+changed.+Refresh+and+try+again.`);
  revalidatePath("/");
  revalidatePath("/payroll");
  revalidatePath(`/payroll/${periodId}`);
  revalidatePath("/payslips");
  redirect(`/payroll/${periodId}?success=Payroll+finalised.+Payslips+are+available.`);
}
