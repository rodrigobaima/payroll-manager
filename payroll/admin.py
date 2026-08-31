from django.contrib import admin

from .models import Company, Employee, PayrollEntry, PayrollPeriod, Payslip, Project, ProjectEmployee, TimesheetEntry


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "currency", "default_payroll_frequency")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "payment_type", "status")
    list_filter = ("payment_type", "status")
    search_fields = ("employee_id", "full_name", "email")


class ProjectEmployeeInline(admin.TabularInline):
    model = ProjectEmployee
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "location", "status")
    list_filter = ("status",)
    search_fields = ("name", "client", "location")
    inlines = (ProjectEmployeeInline,)


@admin.register(TimesheetEntry)
class TimesheetAdmin(admin.ModelAdmin):
    list_display = ("date", "employee", "project", "hours")
    list_filter = ("date", "project")
    search_fields = ("employee__full_name", "project__name")


class PayrollEntryInline(admin.TabularInline):
    model = PayrollEntry
    extra = 0
    readonly_fields = ("employee", "employee_name", "employee_number", "payment_type", "hours_worked", "hourly_rate", "monthly_salary", "gross_pay", "paye", "usc", "prsi", "other_deductions", "total_deductions", "net_pay")
    can_delete = False


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ("start_date", "end_date", "frequency", "pay_date", "status")
    list_filter = ("status", "frequency")
    inlines = (PayrollEntryInline,)


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ("payroll_entry", "file_name", "generated_at")
    readonly_fields = ("payroll_entry", "file_name", "generated_at")

admin.site.site_header = "Payroll Manager administration"
admin.site.site_title = "Payroll Manager"
