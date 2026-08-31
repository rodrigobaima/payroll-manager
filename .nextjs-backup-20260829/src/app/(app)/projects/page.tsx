import Link from "next/link";
import { FolderKanban, Plus } from "lucide-react";
import { completeProjectAction } from "@/app/actions/projects";
import { ConfirmSubmit } from "@/components/confirm-submit";
import { EmptyState } from "@/components/empty-state";
import { FlashMessage } from "@/components/flash-message";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { buttonVariants } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { requireSession } from "@/lib/auth";
import { formatIrishDate } from "@/lib/dates";
import { prisma } from "@/lib/prisma";

export const metadata = { title: "Projects" };
export default async function ProjectsPage({ searchParams }: { searchParams: Promise<{ success?: string; error?: string }> }) { const session = await requireSession(); const [query, projects] = await Promise.all([searchParams, prisma.project.findMany({ where: { companyId: session.companyId }, include: { _count: { select: { employeeLinks: true, timesheets: true } } }, orderBy: [{ status: "asc" }, { name: "asc" }] })]); return <><PageHeader eyebrow="Operations" title="Projects" description="Track active engineering works, assigned staff and recorded hours." actions={<Link href="/projects/new" className={buttonVariants({ size: "lg" })}><Plus />Add project</Link>} /><FlashMessage {...query} />{projects.length ? <div className="data-table-wrap"><Table><TableHeader><TableRow><TableHead>Project</TableHead><TableHead>Location</TableHead><TableHead>Started</TableHead><TableHead>Team / entries</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader><TableBody>{projects.map((project) => <TableRow key={project.id}><TableCell><Link href={`/projects/${project.id}`} className="font-medium hover:text-primary">{project.name}</Link><p className="text-xs text-muted-foreground">{project.client}</p></TableCell><TableCell>{project.location}</TableCell><TableCell>{formatIrishDate(project.startDate)}</TableCell><TableCell>{project._count.employeeLinks} employees · {project._count.timesheets} entries</TableCell><TableCell><StatusBadge status={project.status} /></TableCell><TableCell><div className="flex justify-end gap-2"><Link href={`/projects/${project.id}/edit`} className={buttonVariants({ variant: "outline" })}>Edit</Link>{project.status === "ACTIVE" ? <form action={completeProjectAction.bind(null, project.id)}><ConfirmSubmit message={`Complete ${project.name}? Its history will remain available.`}>Complete</ConfirmSubmit></form> : null}</div></TableCell></TableRow>)}</TableBody></Table></div> : <EmptyState title="No projects yet" description="Create the first active project before recording time." action={<Link href="/projects/new" className={buttonVariants()}><FolderKanban />Create project</Link>} />}</>; }
