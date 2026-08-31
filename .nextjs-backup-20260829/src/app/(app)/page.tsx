import Link from "next/link";
import { AlertCircle, ArrowRight, BriefcaseBusiness, CalendarClock, FileText, Users } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { requireSession } from "@/lib/auth";
import { formatIrishDate } from "@/lib/dates";
import { formatMoney } from "@/lib/money";
import { prisma } from "@/lib/prisma";

export default async function DashboardPage() {
  const session = await requireSession();
  const [employeeCount, activeProjects, currentPeriod, recentPayslips] = await Promise.all([
    prisma.employee.count({ where: { companyId: session.companyId, status: "ACTIVE" } }),
    prisma.project.findMany({ where: { companyId: session.companyId, status: "ACTIVE" }, orderBy: { updatedAt: "desc" }, take: 5 }),
    prisma.payrollPeriod.findFirst({ where: { companyId: session.companyId }, orderBy: { startDate: "desc" }, include: { entries: true } }),
    prisma.payslip.findMany({ where: { payrollEntry: { payrollPeriod: { companyId: session.companyId, status: "FINALISED" } } }, include: { payrollEntry: { include: { payrollPeriod: true } } }, orderBy: { generatedAt: "desc" }, take: 5 }),
  ]);
  const totals = currentPeriod?.entries.reduce((result, entry) => ({ gross: result.gross + Number(entry.grossPay), deductions: result.deductions + Number(entry.totalDeductions), net: result.net + Number(entry.netPay) }), { gross: 0, deductions: 0, net: 0 }) ?? { gross: 0, deductions: 0, net: 0 };
  const employeesWithHours = currentPeriod ? await prisma.timesheetEntry.findMany({ where: { employee: { companyId: session.companyId, status: "ACTIVE" }, date: { gte: currentPeriod.startDate, lte: currentPeriod.endDate } }, distinct: ["employeeId"], select: { employeeId: true } }) : [];
  const missingHours = currentPeriod ? await prisma.employee.findMany({ where: { companyId: session.companyId, status: "ACTIVE", paymentType: "HOURLY", id: { notIn: employeesWithHours.map((row) => row.employeeId) } }, orderBy: { fullName: "asc" } }) : [];

  const stats = [
    ["Active projects", activeProjects.length, BriefcaseBusiness],
    ["Total employees", employeeCount, Users],
    ["Gross payroll", formatMoney(totals.gross), CalendarClock],
    ["Total deductions", formatMoney(totals.deductions), FileText],
    ["Net payroll", formatMoney(totals.net), ArrowRight],
  ] as const;
  return <><PageHeader eyebrow="Overview" title="Payroll at a glance" description={currentPeriod ? `${formatIrishDate(currentPeriod.startDate)} – ${formatIrishDate(currentPeriod.endDate)} · ${currentPeriod.frequency.toLowerCase()} period` : "Create your first payroll period to see current totals."} actions={<><Link href="/timesheets" className={buttonVariants({ variant: "outline", size: "lg" })}>Add timesheet</Link><Link href="/payroll/new" className={buttonVariants({ size: "lg" })}>Run payroll</Link></>} />
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">{stats.map(([label, value, Icon]) => <Card key={label}><CardContent className="p-5"><div className="mb-4 flex items-center justify-between"><span className="text-sm text-muted-foreground">{label}</span><Icon className="size-4 text-primary" /></div><p className="text-2xl font-semibold tracking-tight">{value}</p></CardContent></Card>)}</div>
    <div className="mt-6 grid gap-6 xl:grid-cols-3"><Card className="xl:col-span-2"><CardHeader className="flex-row items-center justify-between"><CardTitle>Current payroll period</CardTitle>{currentPeriod ? <StatusBadge status={currentPeriod.status} /> : null}</CardHeader><CardContent>{currentPeriod ? <div className="grid gap-4 sm:grid-cols-3"><div><p className="text-xs text-muted-foreground">Period</p><p className="mt-1 font-medium">{formatIrishDate(currentPeriod.startDate)} – {formatIrishDate(currentPeriod.endDate)}</p></div><div><p className="text-xs text-muted-foreground">Pay date</p><p className="mt-1 font-medium">{formatIrishDate(currentPeriod.payDate)}</p></div><div><p className="text-xs text-muted-foreground">Employees</p><p className="mt-1 font-medium">{currentPeriod.entries.length}</p></div><Link href={`/payroll/${currentPeriod.id}`} className="inline-flex items-center gap-1 text-sm font-medium text-primary sm:col-span-3">Open payroll <ArrowRight className="size-4" /></Link></div> : <EmptyState title="No payroll periods" description="Create a period after employees and timesheets are ready." />}</CardContent></Card>
    <Card><CardHeader><CardTitle>Missing hours</CardTitle></CardHeader><CardContent>{missingHours.length ? <ul className="space-y-3">{missingHours.map((employee) => <li key={employee.id} className="flex items-center gap-2 text-sm"><AlertCircle className="size-4 text-amber-600" />{employee.fullName}</li>)}</ul> : <p className="text-sm text-muted-foreground">All hourly employees have hours in the current period.</p>}</CardContent></Card></div>
    <div className="mt-6 grid gap-6 xl:grid-cols-2"><Card><CardHeader><CardTitle>Active projects</CardTitle></CardHeader><CardContent>{activeProjects.length ? <ul className="divide-y">{activeProjects.map((project) => <li key={project.id} className="flex items-center justify-between py-3"><div><p className="text-sm font-medium">{project.name}</p><p className="text-xs text-muted-foreground">{project.client} · {project.location}</p></div><Link href={`/projects/${project.id}`} className="text-sm text-primary">View</Link></li>)}</ul> : <EmptyState title="No active projects" description="Add a project to begin recording hours." />}</CardContent></Card>
    <Card><CardHeader><CardTitle>Recent payslips</CardTitle></CardHeader><CardContent>{recentPayslips.length ? <ul className="divide-y">{recentPayslips.map(({ payrollEntry }) => <li key={payrollEntry.id} className="flex items-center justify-between py-3"><div><p className="text-sm font-medium">{payrollEntry.employeeName}</p><p className="text-xs text-muted-foreground">{formatIrishDate(payrollEntry.payrollPeriod.payDate)} · {formatMoney(payrollEntry.netPay.toString())}</p></div><Link href={`/payslips/${payrollEntry.id}`} className="text-sm text-primary">View</Link></li>)}</ul> : <EmptyState title="No payslips yet" description="Payslips become available after finalising payroll." />}</CardContent></Card></div></>;
}
