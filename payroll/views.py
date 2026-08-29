from collections import OrderedDict
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Count, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CompanyForm, DeductionsForm, EmployeeForm, PayrollPeriodForm, ProjectForm, TimesheetForm
from .models import Company, Employee, PayrollEntry, PayrollPeriod, Payslip, Project, TimesheetEntry
from .pdf import build_payslip_pdf
from .services import create_payroll_period, finalise_payroll, review_payroll, update_deductions


def company_or_404():
    company = Company.objects.first()
    if not company:
        raise Http404("Company settings have not been created. Run the development seed first.")
    return company


@login_required
def dashboard(request):
    company = company_or_404()
    period = PayrollPeriod.objects.filter(company=company).prefetch_related("entries").first()
    entries = list(period.entries.all()) if period else []
    active_projects = Project.objects.filter(company=company, status=Project.Status.ACTIVE)
    projects = active_projects
    missing_hours = []
    if period:
        with_hours = TimesheetEntry.objects.filter(employee__company=company, date__range=(period.start_date, period.end_date)).values_list("employee_id", flat=True).distinct()
        missing_hours = Employee.objects.filter(company=company, status=Employee.Status.ACTIVE, payment_type=Employee.PaymentType.HOURLY).exclude(pk__in=with_hours)
    recent_payslips = Payslip.objects.filter(payroll_entry__period__company=company).select_related("payroll_entry", "payroll_entry__period").order_by("-generated_at")[:5]
    return render(request, "payroll/dashboard.html", {
        "period": period, "employee_count": Employee.objects.filter(company=company, status=Employee.Status.ACTIVE).count(),
        "projects": projects, "active_project_count": active_projects.count(),
        "gross_total": sum((entry.gross_pay for entry in entries), Decimal("0")),
        "deductions_total": sum((entry.total_deductions for entry in entries), Decimal("0")),
        "net_total": sum((entry.net_pay for entry in entries), Decimal("0")),
        "missing_hours": missing_hours, "recent_payslips": recent_payslips,
    })


@login_required
def employee_list(request):
    return render(request, "payroll/employees/list.html", {"employees": Employee.objects.filter(company=company_or_404())})


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee.objects.prefetch_related("projects", "timesheets__project", "payroll_entries__period"), pk=pk, company=company_or_404())
    return render(request, "payroll/employees/detail.html", {"employee": employee})


@login_required
def employee_create(request):
    company = company_or_404()
    form = EmployeeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        employee = form.save(commit=False); employee.company = company; employee.save()
        messages.success(request, "Employee created.")
        return redirect("employee-list")
    return render(request, "payroll/form_page.html", {"form": form, "title": "Add employee", "subtitle": "Only payroll-essential details are stored.", "cancel_url": "employee-list"})


@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk, company=company_or_404())
    form = EmployeeForm(request.POST or None, instance=employee)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Employee updated.")
        return redirect("employee-detail", pk=pk)
    return render(request, "payroll/form_page.html", {"form": form, "title": f"Edit {employee.full_name}", "cancel_url": "employee-detail", "cancel_pk": pk})


@login_required
@require_POST
def employee_deactivate(request, pk):
    employee = get_object_or_404(Employee, pk=pk, company=company_or_404())
    employee.status = Employee.Status.INACTIVE; employee.save(update_fields=["status", "updated_at"])
    messages.success(request, "Employee marked inactive. Historical records were preserved.")
    return redirect("employee-list")


@login_required
def project_list(request):
    projects = Project.objects.filter(company=company_or_404()).annotate(employee_count=Count("employees"), timesheet_count=Count("timesheets", distinct=True))
    return render(request, "payroll/projects/list.html", {"projects": projects})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project.objects.prefetch_related("employees", "timesheets__employee"), pk=pk, company=company_or_404())
    return render(request, "payroll/projects/detail.html", {"project": project, "total_hours": project.timesheets.aggregate(total=Sum("hours"))["total"] or Decimal("0")})


@login_required
def project_create(request):
    company = company_or_404(); form = ProjectForm(request.POST or None, company=company)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False); project.company = company; project.save(); project.employees.set(form.cleaned_data["employees"])
        messages.success(request, "Project created."); return redirect("project-list")
    return render(request, "payroll/form_page.html", {"form": form, "title": "Add project", "cancel_url": "project-list"})


@login_required
def project_edit(request, pk):
    company = company_or_404(); project = get_object_or_404(Project, pk=pk, company=company)
    form = ProjectForm(request.POST or None, instance=project, company=company)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Project updated."); return redirect("project-detail", pk=pk)
    return render(request, "payroll/form_page.html", {"form": form, "title": f"Edit {project.name}", "cancel_url": "project-detail", "cancel_pk": pk})


@login_required
@require_POST
def project_complete(request, pk):
    project = get_object_or_404(Project, pk=pk, company=company_or_404())
    project.status = Project.Status.COMPLETED; project.save(update_fields=["status", "updated_at"])
    messages.success(request, "Project completed. Timesheet history was preserved.")
    return redirect("project-list")


def week_range(value):
    monday = value - timedelta(days=value.weekday())
    return monday, monday + timedelta(days=6)


@login_required
def timesheet_list(request):
    company = company_or_404()
    try: selected = datetime.strptime(request.GET.get("week", ""), "%Y-%m-%d").date()
    except ValueError: selected = date.today()
    start, end = week_range(selected)
    form = TimesheetForm(request.POST or None, company=company, initial={"date": date.today()})
    if request.method == "POST" and form.is_valid():
        try:
            entry = form.save(); entry.project.employees.add(entry.employee)
            messages.success(request, "Timesheet entry added.")
            return redirect(f"/timesheets/?week={entry.date:%Y-%m-%d}")
        except IntegrityError: form.add_error(None, "An entry already exists for that employee, project and date.")
    entries = TimesheetEntry.objects.filter(employee__company=company, date__range=(start, end)).select_related("employee", "project").order_by("employee__full_name", "date", "project__name")
    grouped = OrderedDict()
    for entry in entries:
        employee_group = grouped.setdefault(entry.employee, {"days": OrderedDict(), "total": Decimal("0")})
        day_entries = employee_group["days"].setdefault(entry.date, {"entries": [], "total": Decimal("0")})
        day_entries["entries"].append(entry); day_entries["total"] += entry.hours; employee_group["total"] += entry.hours
    return render(request, "payroll/timesheets.html", {"form": form, "grouped": grouped, "week_start": start, "week_end": end, "previous_week": start - timedelta(days=7), "next_week": start + timedelta(days=7)})


@login_required
@require_POST
def timesheet_delete(request, pk):
    entry = get_object_or_404(TimesheetEntry, pk=pk, employee__company=company_or_404()); selected = entry.date; entry.delete()
    messages.success(request, "Timesheet entry removed.")
    return redirect(f"/timesheets/?week={selected:%Y-%m-%d}")


@login_required
def payroll_list(request):
    periods = PayrollPeriod.objects.filter(company=company_or_404()).annotate(
        gross_total=Sum("entries__gross_pay"), deductions_total=Sum("entries__total_deductions"), net_total=Sum("entries__net_pay")
    ).prefetch_related("entries")
    return render(request, "payroll/payroll/list.html", {"periods": periods})


@login_required
def payroll_create(request):
    company = company_or_404(); form = PayrollPeriodForm(request.POST or None, initial={"frequency": company.default_payroll_frequency})
    if request.method == "POST" and form.is_valid():
        if not Employee.objects.filter(company=company, status=Employee.Status.ACTIVE).exists(): form.add_error(None, "Add an active employee before running payroll.")
        else:
            try:
                period = create_payroll_period(company=company, **form.cleaned_data); messages.success(request, "Draft payroll created from timesheets.")
                return redirect("payroll-detail", pk=period.pk)
            except (IntegrityError, ValidationError) as error: form.add_error(None, error.messages[0] if hasattr(error, "messages") else "That payroll period already exists.")
    return render(request, "payroll/form_page.html", {"form": form, "title": "Run payroll", "subtitle": "Gross pay is calculated now. PAYE, USC and PRSI remain manual.", "cancel_url": "payroll-list"})


@login_required
def payroll_detail(request, pk):
    period = get_object_or_404(PayrollPeriod.objects.prefetch_related("entries"), pk=pk, company=company_or_404()); entries = list(period.entries.all())
    return render(request, "payroll/payroll/detail.html", {"period": period, "entries": entries, "gross_total": sum((e.gross_pay for e in entries), Decimal("0")), "deductions_total": sum((e.total_deductions for e in entries), Decimal("0")), "net_total": sum((e.net_pay for e in entries), Decimal("0"))})


@login_required
@require_POST
def payroll_deductions(request, pk, entry_pk):
    period = get_object_or_404(PayrollPeriod, pk=pk, company=company_or_404()); entry = get_object_or_404(PayrollEntry, pk=entry_pk, period=period); form = DeductionsForm(request.POST)
    if form.is_valid():
        try: update_deductions(entry_id=entry.pk, **form.cleaned_data); messages.success(request, f"Deductions updated for {entry.employee_name}.")
        except ValidationError as error: messages.error(request, error.messages[0])
    else: messages.error(request, "Enter valid non-negative deduction values.")
    return redirect("payroll-detail", pk=pk)


@login_required
@require_POST
def payroll_review(request, pk):
    get_object_or_404(PayrollPeriod, pk=pk, company=company_or_404())
    try: review_payroll(pk); messages.success(request, "Payroll marked as reviewed. Check the summary before finalising.")
    except ValidationError as error: messages.error(request, error.messages[0])
    return redirect("payroll-detail", pk=pk)


@login_required
@require_POST
def payroll_finalise(request, pk):
    get_object_or_404(PayrollPeriod, pk=pk, company=company_or_404())
    try: finalise_payroll(pk); messages.success(request, "Payroll finalised. Payslips are now locked and available.")
    except ValidationError as error: messages.error(request, error.messages[0])
    return redirect("payroll-detail", pk=pk)


@login_required
def payslip_list(request):
    payslips = Payslip.objects.filter(payroll_entry__period__company=company_or_404(), payroll_entry__period__status=PayrollPeriod.Status.FINALISED).select_related("payroll_entry", "payroll_entry__period")
    return render(request, "payroll/payslips/list.html", {"payslips": payslips})


@login_required
def payslip_detail(request, entry_pk):
    entry = get_object_or_404(PayrollEntry.objects.select_related("period", "employee"), pk=entry_pk, period__company=company_or_404(), period__status=PayrollPeriod.Status.FINALISED)
    return render(request, "payroll/payslips/detail.html", {"entry": entry, "company": entry.period.company})


@login_required
def payslip_pdf(request, entry_pk):
    entry = get_object_or_404(PayrollEntry.objects.select_related("period", "period__company"), pk=entry_pk, period__company=company_or_404(), period__status=PayrollPeriod.Status.FINALISED)
    payslip, _ = Payslip.objects.get_or_create(payroll_entry=entry, defaults={"file_name": f"{entry.employee_number}-{entry.period.pay_date:%Y-%m-%d}-payslip.pdf"})
    response = HttpResponse(build_payslip_pdf(entry), content_type="application/pdf"); disposition = "inline" if request.GET.get("preview") == "1" else "attachment"
    response["Content-Disposition"] = f'{disposition}; filename="{payslip.file_name}"'; return response


@login_required
def settings_view(request):
    company = Company.objects.first(); form = CompanyForm(request.POST or None, instance=company)
    if request.method == "POST" and form.is_valid(): form.save(); messages.success(request, "Company settings saved."); return redirect("settings")
    return render(request, "payroll/settings.html", {"form": form})
