import Link from "next/link";
import { Plus, Users } from "lucide-react";
import { deactivateEmployeeAction } from "@/app/actions/employees";
import { ConfirmSubmit } from "@/components/confirm-submit";
import { EmptyState } from "@/components/empty-state";
import { FlashMessage } from "@/components/flash-message";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { buttonVariants } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { requireSession } from "@/lib/auth";
import { formatMoney } from "@/lib/money";
import { prisma } from "@/lib/prisma";

export const metadata = { title: "Employees" };
export default async function EmployeesPage({ searchParams }: { searchParams: Promise<{ success?: string; error?: string }> }) {
  const session = await requireSession();
  const [params, employees] = await Promise.all([searchParams, prisma.employee.findMany({ where: { companyId: session.companyId }, orderBy: [{ status: "asc" }, { fullName: "asc" }] })]);
  return <><PageHeader eyebrow="People" title="Employees" description="Manage the small team included in payroll." actions={<Link href="/employees/new" className={buttonVariants({ size: "lg" })}><Plus />Add employee</Link>} /><FlashMessage {...params} />{employees.length ? <div className="data-table-wrap"><Table><TableHeader><TableRow><TableHead>Employee</TableHead><TableHead>Payment</TableHead><TableHead>Rate / salary</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader><TableBody>{employees.map((employee) => <TableRow key={employee.id}><TableCell><Link className="font-medium hover:text-primary" href={`/employees/${employee.id}`}>{employee.fullName}</Link><p className="text-xs text-muted-foreground">{employee.employeeId} · {employee.email}</p></TableCell><TableCell className="capitalize">{employee.paymentType.toLowerCase()}</TableCell><TableCell>{employee.paymentType === "HOURLY" ? `${formatMoney(employee.hourlyRate!.toString())}/h` : `${formatMoney(employee.monthlySalary!.toString())}/month`}</TableCell><TableCell><StatusBadge status={employee.status} /></TableCell><TableCell><div className="flex justify-end gap-2"><Link href={`/employees/${employee.id}/edit`} className={buttonVariants({ variant: "outline" })}>Edit</Link>{employee.status === "ACTIVE" ? <form action={deactivateEmployeeAction.bind(null, employee.id)}><ConfirmSubmit message={`Mark ${employee.fullName} inactive? Existing payroll history will be preserved.`}>Deactivate</ConfirmSubmit></form> : null}</div></TableCell></TableRow>)}</TableBody></Table></div> : <EmptyState title="No employees yet" description="Add an employee before recording timesheets or running payroll." action={<Link href="/employees/new" className={buttonVariants()}><Users />Add first employee</Link>} />}</>;
}
