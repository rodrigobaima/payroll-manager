import Link from "next/link";
import { createProjectAction } from "@/app/actions/projects";
import { FlashMessage } from "@/components/flash-message";
import { PageHeader } from "@/components/page-header";
import { ProjectForm } from "@/components/project-form";
import { buttonVariants } from "@/components/ui/button";
import { requireSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export const metadata = { title: "Add project" };
export default async function NewProjectPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) { const session = await requireSession(); const [query, employees] = await Promise.all([searchParams, prisma.employee.findMany({ where: { companyId: session.companyId, status: "ACTIVE" }, orderBy: { fullName: "asc" } })]); return <><PageHeader title="Add project" description="Assign employees now or let assignments be created from timesheets." actions={<Link href="/projects" className={buttonVariants({ variant: "outline" })}>Cancel</Link>} /><FlashMessage {...query} /><ProjectForm employees={employees} action={createProjectAction} /></>; }
