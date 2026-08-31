import { z } from "zod";

const optionalText = z
  .string()
  .trim()
  .transform((value) => (value === "" ? undefined : value))
  .optional();

export const employeeSchema = z
  .object({
    fullName: z.string().trim().min(2).max(191),
    employeeId: z.string().trim().min(1).max(50),
    email: z.email().max(191),
    phone: optionalText,
    paymentType: z.enum(["HOURLY", "MONTHLY"]),
    hourlyRate: optionalText,
    monthlySalary: optionalText,
    startDate: z.iso.date(),
    status: z.enum(["ACTIVE", "INACTIVE"]),
  })
  .superRefine((data, ctx) => {
    if (data.paymentType === "HOURLY") {
      const rate = Number(data.hourlyRate);
      if (!data.hourlyRate || !Number.isFinite(rate) || rate < 0) {
        ctx.addIssue({ code: "custom", path: ["hourlyRate"], message: "Hourly rate is required and must be non-negative." });
      }
    }
    if (data.paymentType === "MONTHLY") {
      const salary = Number(data.monthlySalary);
      if (!data.monthlySalary || !Number.isFinite(salary) || salary < 0) {
        ctx.addIssue({ code: "custom", path: ["monthlySalary"], message: "Monthly salary is required and must be non-negative." });
      }
    }
  });

export const projectSchema = z.object({
  name: z.string().trim().min(2).max(191),
  client: z.string().trim().min(2).max(191),
  location: z.string().trim().min(2).max(191),
  startDate: z.iso.date(),
  status: z.enum(["ACTIVE", "COMPLETED"]),
  notes: optionalText,
  employeeIds: z.array(z.string()).default([]),
});

export const timesheetSchema = z.object({
  employeeId: z.string().min(1),
  projectId: z.string().min(1),
  date: z.iso.date(),
  hours: z.coerce.number().positive().max(24),
});

export const payrollPeriodSchema = z
  .object({
    frequency: z.enum(["WEEKLY", "MONTHLY"]),
    startDate: z.iso.date(),
    endDate: z.iso.date(),
    payDate: z.iso.date(),
  })
  .refine((data) => data.endDate >= data.startDate, {
    path: ["endDate"],
    message: "End date must be on or after start date.",
  });

export const deductionsSchema = z.object({
  payrollEntryId: z.string().min(1),
  paye: z.coerce.number().min(0),
  usc: z.coerce.number().min(0),
  prsi: z.coerce.number().min(0),
  otherDeductions: z.coerce.number().min(0),
});

export const settingsSchema = z.object({
  companyName: z.string().trim().min(2).max(191),
  companyAddress: z.string().trim().min(5).max(2000),
  currency: z.literal("EUR"),
  defaultPayrollFrequency: z.enum(["WEEKLY", "MONTHLY"]),
});

export function formDataObject(formData: FormData) {
  return Object.fromEntries(formData.entries());
}

export function firstZodError(error: z.ZodError) {
  return error.issues[0]?.message ?? "Please check the submitted values.";
}

