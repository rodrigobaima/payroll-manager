import Link from "next/link";
import { createEmployeeAction } from "@/app/actions/employees";
import { EmployeeForm } from "@/components/employee-form";
import { FlashMessage } from "@/components/flash-message";
import { PageHeader } from "@/components/page-header";
import { buttonVariants } from "@/components/ui/button";

export const metadata = { title: "Add employee" };
export default async function NewEmployeePage({ searchParams }: { searchParams: Promise<{ error?: string }> }) { const params = await searchParams; return <><PageHeader title="Add employee" description="Only payroll-essential details are collected. PPS and bank data are not stored." actions={<Link href="/employees" className={buttonVariants({ variant: "outline" })}>Cancel</Link>} /><FlashMessage {...params} /><EmployeeForm action={createEmployeeAction} /></>; }
