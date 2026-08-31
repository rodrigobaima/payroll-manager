import Link from "next/link";
import { notFound } from "next/navigation";
import { updateEmployeeAction } from "@/app/actions/employees";
import { EmployeeForm } from "@/components/employee-form";
import { FlashMessage } from "@/components/flash-message";
import { PageHeader } from "@/components/page-header";
import { buttonVariants } from "@/components/ui/button";
import { requireSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export default async function EditEmployeePage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<{ error?: string }> }) { const [{ id }, query, session] = await Promise.all([params, searchParams, requireSession()]); const employee = await prisma.employee.findFirst({ where: { id, companyId: session.companyId } }); if (!employee) notFound(); return <><PageHeader title={`Edit ${employee.fullName}`} actions={<Link href={`/employees/${id}`} className={buttonVariants({ variant: "outline" })}>Cancel</Link>} /><FlashMessage {...query} /><EmployeeForm employee={employee} action={updateEmployeeAction.bind(null, id)} /></>; }
