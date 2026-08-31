import { describe, expect, it } from "vitest";
import {
  calculateHourlyGross,
  calculateMonthlyGross,
  calculateNetPay,
  PayrollCalculationError,
} from "./money";
import { assertPayrollEditable, calculateGrossForEmployee } from "./payroll";

describe("payroll calculations", () => {
  it("calculates the required hourly employee example exactly", () => {
    const gross = calculateHourlyGross("40", "20.00");
    const result = calculateNetPay(gross, {
      paye: "100.00",
      usc: "25.00",
      prsi: "32.00",
      otherDeductions: "0",
    });
    expect(gross.toFixed(2)).toBe("800.00");
    expect(result.totalDeductions.toFixed(2)).toBe("157.00");
    expect(result.netPay.toFixed(2)).toBe("643.00");
  });

  it("does not use hours for a monthly employee", () => {
    expect(calculateMonthlyGross("4000").toFixed(2)).toBe("4000.00");
    expect(
      calculateGrossForEmployee({
        paymentType: "MONTHLY",
        hoursWorked: "999",
        hourlyRate: null,
        monthlySalary: "4000",
      }).toFixed(2),
    ).toBe("4000.00");
  });

  it("sums hours from multiple projects before calculating gross", () => {
    const totalHours = ["20", "20"].reduce(
      (sum, value) => sum + Number(value),
      0,
    );
    expect(calculateHourlyGross(totalHours, "20").toFixed(2)).toBe("800.00");
  });

  it("preserves decimal hour precision", () => {
    expect(calculateHourlyGross("7.5", "20").toFixed(2)).toBe("150.00");
  });

  it.each([
    () => calculateHourlyGross("-1", "20"),
    () => calculateHourlyGross("1", "-20"),
    () => calculateHourlyGross("invalid", "20"),
    () => calculateNetPay("100", { paye: "-1", usc: 0, prsi: 0, otherDeductions: 0 }),
    () => calculateNetPay("100", { paye: "101", usc: 0, prsi: 0, otherDeductions: 0 }),
  ])("rejects invalid financial values", (operation) => {
    expect(operation).toThrow(PayrollCalculationError);
  });

  it("prevents a finalised payroll from being changed", () => {
    expect(() => assertPayrollEditable("FINALISED")).toThrow(
      "Finalised payroll cannot be changed.",
    );
    expect(() => assertPayrollEditable("DRAFT")).not.toThrow();
  });
});
