from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Company(models.Model):
    name = models.CharField(max_length=191)
    address = models.TextField()
    currency = models.CharField(max_length=3, choices=[("EUR", "EUR (€)")], default="EUR")
    default_payroll_frequency = models.CharField(max_length=10, choices=[("WEEKLY", "Weekly"), ("MONTHLY", "Monthly")], default="WEEKLY")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name


class Employee(models.Model):
    class PaymentType(models.TextChoices):
        HOURLY = "HOURLY", "Hourly"
        MONTHLY = "MONTHLY", "Monthly"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="employees")
    full_name = models.CharField(max_length=191, db_index=True)
    employee_id = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True)
    payment_type = models.CharField(max_length=10, choices=PaymentType.choices)
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]
        constraints = [
            models.CheckConstraint(condition=Q(hourly_rate__gte=0) | Q(hourly_rate__isnull=True), name="employee_hourly_rate_non_negative"),
            models.CheckConstraint(condition=Q(monthly_salary__gte=0) | Q(monthly_salary__isnull=True), name="employee_monthly_salary_non_negative"),
        ]

    def clean(self):
        errors = {}
        if self.payment_type == self.PaymentType.HOURLY:
            if self.hourly_rate is None:
                errors["hourly_rate"] = "Hourly rate is required for hourly employees."
            if self.monthly_salary is not None:
                errors["monthly_salary"] = "Monthly salary must be empty for hourly employees."
        elif self.payment_type == self.PaymentType.MONTHLY:
            if self.monthly_salary is None:
                errors["monthly_salary"] = "Monthly salary is required for monthly employees."
            if self.hourly_rate is not None:
                errors["hourly_rate"] = "Hourly rate must be empty for monthly employees."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"


class Project(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="projects")
    name = models.CharField(max_length=191, db_index=True)
    client = models.CharField(max_length=191)
    location = models.CharField(max_length=191)
    start_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    notes = models.TextField(blank=True)
    employees = models.ManyToManyField(Employee, through="ProjectEmployee", related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProjectEmployee(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="employee_links")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="project_links")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["project", "employee"], name="unique_project_employee")]
        indexes = [models.Index(fields=["employee", "project"])]


class TimesheetEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="timesheets")
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="timesheets")
    date = models.DateField(db_index=True)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "employee__full_name"]
        constraints = [
            models.CheckConstraint(condition=Q(hours__gt=0) & Q(hours__lte=24), name="timesheet_hours_valid"),
            models.UniqueConstraint(fields=["employee", "project", "date"], name="unique_timesheet_employee_project_date"),
        ]
        indexes = [models.Index(fields=["employee", "date"]), models.Index(fields=["project", "date"])]

    def __str__(self):
        return f"{self.employee} - {self.date}: {self.hours}h"


class PayrollPeriod(models.Model):
    class Frequency(models.TextChoices):
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        REVIEWED = "REVIEWED", "Reviewed"
        FINALISED = "FINALISED", "Finalised"

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="payroll_periods")
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    pay_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    finalised_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(fields=["company", "frequency", "start_date", "end_date"], name="unique_payroll_period"),
            models.CheckConstraint(condition=Q(end_date__gte=models.F("start_date")), name="payroll_period_dates_valid"),
        ]

    def __str__(self):
        return f"{self.get_frequency_display()} {self.start_date} - {self.end_date}"

    def save(self, *args, **kwargs):
        if self.pk:
            current = PayrollPeriod.objects.filter(pk=self.pk).values(
                "company_id", "frequency", "start_date", "end_date", "pay_date", "status"
            ).first()
            if current and current["status"] == self.Status.FINALISED:
                protected = {
                    "company_id": self.company_id, "frequency": self.frequency,
                    "start_date": self.start_date, "end_date": self.end_date,
                    "pay_date": self.pay_date, "status": self.status,
                }
                if current != protected:
                    raise ValidationError("Finalised payroll periods cannot be changed.")
        return super().save(*args, **kwargs)


class PayrollEntry(models.Model):
    period = models.ForeignKey(PayrollPeriod, on_delete=models.PROTECT, related_name="entries")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="payroll_entries")
    employee_name = models.CharField(max_length=191)
    employee_number = models.CharField(max_length=50)
    payment_type = models.CharField(max_length=10, choices=Employee.PaymentType.choices)
    hours_worked = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2)
    paye = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    usc = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    prsi = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee_name"]
        constraints = [
            models.UniqueConstraint(fields=["period", "employee"], name="unique_payroll_employee_period"),
            models.CheckConstraint(condition=Q(hours_worked__gte=0), name="payroll_hours_non_negative"),
            models.CheckConstraint(condition=Q(gross_pay__gte=0), name="payroll_gross_non_negative"),
            models.CheckConstraint(condition=Q(paye__gte=0) & Q(usc__gte=0) & Q(prsi__gte=0) & Q(other_deductions__gte=0), name="payroll_deductions_non_negative"),
            models.CheckConstraint(condition=Q(total_deductions__lte=models.F("gross_pay")), name="payroll_deductions_not_above_gross"),
            models.CheckConstraint(condition=Q(net_pay__gte=0), name="payroll_net_non_negative"),
        ]

    def save(self, *args, **kwargs):
        if self.pk and PayrollEntry.objects.filter(pk=self.pk, period__status=PayrollPeriod.Status.FINALISED).exists():
            raise ValidationError("Finalised payroll entries cannot be changed.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_name} - {self.period}"


class Payslip(models.Model):
    payroll_entry = models.OneToOneField(PayrollEntry, on_delete=models.PROTECT, related_name="payslip")
    file_name = models.CharField(max_length=191)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file_name
