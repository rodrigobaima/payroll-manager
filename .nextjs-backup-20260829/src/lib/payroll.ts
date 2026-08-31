import { PayrollStatus, PaymentType } from "@prisma/client";
import { calculateHourlyGross, calculateMonthlyGross } from "./money";

export class PayrollStateError extends Error {}

export function assertPayrollEditable(status: PayrollStatus | string) {
  if (status === PayrollStatus.FINALISED || status === "FINALISED") {
    throw new PayrollStateError("Finalised payroll cannot be changed.");
  }
}

export function calculateGrossForEmployee(input: {
  paymentType: PaymentType | "HOURLY" | "MONTHLY";
  hoursWorked: string;
  hourlyRate: string | null;
  monthlySalary: string | null;
}) {
  if (input.paymentType === "HOURLY") {
    if (input.hourlyRate === null) throw new Error("Hourly rate is missing.");
    return calculateHourlyGross(input.hoursWorked, input.hourlyRate);
  }
  if (input.monthlySalary === null) throw new Error("Monthly salary is missing.");
  return calculateMonthlyGross(input.monthlySalary);
}

