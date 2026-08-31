import { PrismaClient, PayrollStatus } from "@prisma/client";
import { hash } from "bcryptjs";
import {
  calculateHourlyGross,
  calculateMonthlyGross,
  calculateNetPay,
} from "../src/lib/money";

const prisma = new PrismaClient();

const employeeSeed = [
  { employeeId: "ENG-001", fullName: "Aoife Brennan", email: "aoife.brennan@example.ie", paymentType: "HOURLY" as const, hourlyRate: "24.50" },
  { employeeId: "ENG-002", fullName: "Cian Murphy", email: "cian.murphy@example.ie", paymentType: "HOURLY" as const, hourlyRate: "22.00" },
  { employeeId: "ENG-003", fullName: "Niamh O'Connor", email: "niamh.oconnor@example.ie", paymentType: "HOURLY" as const, hourlyRate: "26.75" },
  { employeeId: "ENG-004", fullName: "Darragh Kelly", email: "darragh.kelly@example.ie", paymentType: "HOURLY" as const, hourlyRate: "21.50" },
  { employeeId: "ENG-005", fullName: "Saoirse Byrne", email: "saoirse.byrne@example.ie", paymentType: "HOURLY" as const, hourlyRate: "25.00" },
  { employeeId: "ENG-006", fullName: "Eoin Walsh", email: "eoin.walsh@example.ie", paymentType: "MONTHLY" as const, monthlySalary: "4800.00" },
  { employeeId: "ENG-007", fullName: "Orla Ryan", email: "orla.ryan@example.ie", paymentType: "MONTHLY" as const, monthlySalary: "5200.00" },
];

const projectSeed = [
  ["Harbour Quay Retrofit", "Atlantic Property Group", "Dublin 2"],
  ["Liffey Bridge Survey", "Dublin Civil Works", "Dublin 8"],
  ["Cork Innovation Campus", "Munster Developments", "Cork City"],
  ["Galway Water Upgrade", "West Utilities", "Galway City"],
  ["Kilkenny Civic Centre", "Kilkenny Council", "Kilkenny"],
  ["Sligo Coastal Works", "Northwest Infrastructure", "Sligo"],
  ["Limerick Logistics Hub", "Shannon Commercial", "Limerick"],
];

async function main() {
  const adminEmail = process.env.SEED_ADMIN_EMAIL ?? "admin@example.ie";
  const adminPassword = process.env.SEED_ADMIN_PASSWORD;
  if (!adminPassword || adminPassword.length < 12) {
    throw new Error("SEED_ADMIN_PASSWORD must be set to at least 12 characters before seeding.");
  }

  await prisma.payslip.deleteMany();
  await prisma.payrollEntry.deleteMany();
  await prisma.payrollPeriod.deleteMany();
  await prisma.timesheetEntry.deleteMany();
  await prisma.projectEmployee.deleteMany();
  await prisma.project.deleteMany();
  await prisma.employee.deleteMany();
  await prisma.settings.deleteMany();
  await prisma.user.deleteMany();
  await prisma.company.deleteMany();

  const company = await prisma.company.create({
    data: {
      name: "Northstar Engineering Services",
      address: "14 Harbour View, Dublin 2, Ireland",
      settings: { create: { currency: "EUR", defaultPayrollFrequency: "WEEKLY" } },
      users: {
        create: {
          name: "Payroll Administrator",
          email: adminEmail.toLowerCase(),
          passwordHash: await hash(adminPassword, 12),
        },
      },
    },
  });

  const employees = [];
  for (const employee of employeeSeed) {
    employees.push(
      await prisma.employee.create({
        data: {
          companyId: company.id,
          employeeId: employee.employeeId,
          fullName: employee.fullName,
          email: employee.email,
          paymentType: employee.paymentType,
          hourlyRate: employee.paymentType === "HOURLY" ? employee.hourlyRate : null,
          monthlySalary: employee.paymentType === "MONTHLY" ? employee.monthlySalary : null,
          startDate: new Date("2025-01-06T00:00:00.000Z"),
          status: "ACTIVE",
        },
      }),
    );
  }

  const projects = [];
  for (const [name, client, location] of projectSeed) {
    projects.push(
      await prisma.project.create({
        data: {
          companyId: company.id,
          name,
          client,
          location,
          startDate: new Date("2026-02-02T00:00:00.000Z"),
          status: "ACTIVE",
          notes: "Fictitious demonstration project.",
        },
      }),
    );
  }

  for (let employeeIndex = 0; employeeIndex < employees.length; employeeIndex += 1) {
    for (const projectIndex of [employeeIndex % 7, (employeeIndex + 1) % 7]) {
      await prisma.projectEmployee.create({
        data: { employeeId: employees[employeeIndex].id, projectId: projects[projectIndex].id },
      });
    }
  }

  const workDays = [24, 25, 26, 27, 28];
  for (let employeeIndex = 0; employeeIndex < employees.length; employeeIndex += 1) {
    for (const day of workDays) {
      const employee = employees[employeeIndex];
      const firstProject = projects[employeeIndex % 7];
      const secondProject = projects[(employeeIndex + 1) % 7];
      await prisma.timesheetEntry.createMany({
        data: [
          { employeeId: employee.id, projectId: firstProject.id, date: new Date(`2026-08-${day}T00:00:00.000Z`), hours: "4.00" },
          { employeeId: employee.id, projectId: secondProject.id, date: new Date(`2026-08-${day}T00:00:00.000Z`), hours: "4.00" },
        ],
      });
    }
  }

  const period = await prisma.payrollPeriod.create({
    data: {
      companyId: company.id,
      frequency: "MONTHLY",
      startDate: new Date("2026-08-01T00:00:00.000Z"),
      endDate: new Date("2026-08-31T00:00:00.000Z"),
      payDate: new Date("2026-08-31T00:00:00.000Z"),
      status: PayrollStatus.FINALISED,
      reviewedAt: new Date(),
      finalisedAt: new Date(),
    },
  });

  for (const employee of employees) {
    const hoursWorked = "40.00";
    const gross =
      employee.paymentType === "HOURLY"
        ? calculateHourlyGross(hoursWorked, employee.hourlyRate!.toString())
        : calculateMonthlyGross(employee.monthlySalary!.toString());
    const deductions = calculateNetPay(gross, {
      paye: gross.mul("0.12"),
      usc: gross.mul("0.03"),
      prsi: gross.mul("0.04"),
      otherDeductions: "0",
    });
    const entry = await prisma.payrollEntry.create({
      data: {
        payrollPeriodId: period.id,
        employeeId: employee.id,
        employeeName: employee.fullName,
        employeeNumber: employee.employeeId,
        paymentType: employee.paymentType,
        hoursWorked,
        hourlyRate: employee.hourlyRate,
        monthlySalary: employee.monthlySalary,
        grossPay: gross.toFixed(2),
        paye: deductions.paye.toFixed(2),
        usc: deductions.usc.toFixed(2),
        prsi: deductions.prsi.toFixed(2),
        otherDeductions: deductions.otherDeductions.toFixed(2),
        totalDeductions: deductions.totalDeductions.toFixed(2),
        netPay: deductions.netPay.toFixed(2),
      },
    });
    await prisma.payslip.create({
      data: { payrollEntryId: entry.id, fileName: `${employee.employeeId}-2026-08-payslip.pdf` },
    });
  }

  console.log(`Seeded 1 company, ${employees.length} employees, ${projects.length} projects and 1 finalised payroll.`);
  console.log(`Development login email: ${adminEmail}`);
}

main()
  .catch((error) => {
    console.error(error instanceof Error ? error.message : "Seed failed.");
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
