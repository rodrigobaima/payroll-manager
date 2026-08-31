import Decimal from "decimal.js";

Decimal.set({ precision: 28, rounding: Decimal.ROUND_HALF_UP });

export type MoneyInput = Decimal.Value;

export class PayrollCalculationError extends Error {}

export function decimal(value: MoneyInput, field = "Value") {
  let result: Decimal;
  try {
    result = new Decimal(value);
  } catch {
    throw new PayrollCalculationError(`${field} must be a valid number.`);
  }
  if (!result.isFinite()) {
    throw new PayrollCalculationError(`${field} must be a finite number.`);
  }
  return result;
}

export function money(value: MoneyInput) {
  return decimal(value).toDecimalPlaces(2, Decimal.ROUND_HALF_UP);
}

export function nonNegative(value: MoneyInput, field: string) {
  const result = decimal(value, field);
  if (result.isNegative()) {
    throw new PayrollCalculationError(`${field} cannot be negative.`);
  }
  return result;
}

export function calculateHourlyGross(hours: MoneyInput, hourlyRate: MoneyInput) {
  const safeHours = nonNegative(hours, "Hours");
  const safeRate = nonNegative(hourlyRate, "Hourly rate");
  return money(safeHours.mul(safeRate));
}

export function calculateMonthlyGross(monthlySalary: MoneyInput) {
  return money(nonNegative(monthlySalary, "Monthly salary"));
}

export interface DeductionInput {
  paye: MoneyInput;
  usc: MoneyInput;
  prsi: MoneyInput;
  otherDeductions: MoneyInput;
}

export function calculateNetPay(grossPay: MoneyInput, input: DeductionInput) {
  const gross = money(nonNegative(grossPay, "Gross pay"));
  const paye = money(nonNegative(input.paye, "PAYE"));
  const usc = money(nonNegative(input.usc, "USC"));
  const prsi = money(nonNegative(input.prsi, "PRSI"));
  const otherDeductions = money(
    nonNegative(input.otherDeductions, "Other deductions"),
  );
  const totalDeductions = money(paye.add(usc).add(prsi).add(otherDeductions));

  if (totalDeductions.greaterThan(gross)) {
    throw new PayrollCalculationError(
      "Total deductions cannot exceed gross pay in this MVP.",
    );
  }

  return {
    paye,
    usc,
    prsi,
    otherDeductions,
    totalDeductions,
    netPay: money(gross.sub(totalDeductions)),
  };
}

export function formatMoney(value: MoneyInput) {
  return new Intl.NumberFormat("en-IE", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(decimal(value).toNumber());
}

