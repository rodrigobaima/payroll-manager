from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum

from .models import Company, Employee, PayrollPeriod, Project, TimesheetEntry


class DateInput(forms.DateInput):
    input_type = "date"


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["full_name", "employee_id", "email", "phone", "payment_type", "hourly_rate", "monthly_salary", "start_date", "status"]
        widgets = {"start_date": DateInput()}

    def clean(self):
        cleaned = super().clean()
        payment_type = cleaned.get("payment_type")
        if payment_type == Employee.PaymentType.HOURLY:
            cleaned["monthly_salary"] = None
            if cleaned.get("hourly_rate") is None:
                self.add_error("hourly_rate", "Hourly rate is required.")
        elif payment_type == Employee.PaymentType.MONTHLY:
            cleaned["hourly_rate"] = None
            if cleaned.get("monthly_salary") is None:
                self.add_error("monthly_salary", "Monthly salary is required.")
        return cleaned


class ProjectForm(forms.ModelForm):
    employees = forms.ModelMultipleChoiceField(queryset=Employee.objects.none(), required=False, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Project
        fields = ["name", "client", "location", "start_date", "status", "notes", "employees"]
        widgets = {"start_date": DateInput(), "notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employees"].queryset = Employee.objects.filter(company=company).order_by("full_name")
        if self.instance.pk:
            self.fields["employees"].initial = self.instance.employees.all()

    def save(self, commit=True):
        project = super().save(commit)
        if commit:
            project.employees.set(self.cleaned_data["employees"])
        return project


class TimesheetForm(forms.ModelForm):
    class Meta:
        model = TimesheetEntry
        fields = ["employee", "project", "date", "hours"]
        widgets = {"date": DateInput(), "hours": forms.NumberInput(attrs={"min": "0.01", "max": "24", "step": "0.25"})}

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        self.fields["employee"].queryset = Employee.objects.filter(company=company, status=Employee.Status.ACTIVE)
        self.fields["project"].queryset = Project.objects.filter(company=company, status=Project.Status.ACTIVE)

    def clean(self):
        cleaned = super().clean()
        employee, date, hours = cleaned.get("employee"), cleaned.get("date"), cleaned.get("hours")
        if employee and date and hours:
            query = TimesheetEntry.objects.filter(employee=employee, date=date)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            daily = query.aggregate(total=Sum("hours"))["total"] or Decimal("0")
            if daily + hours > Decimal("24"):
                raise ValidationError("Total daily hours cannot exceed 24.")
        return cleaned


class PayrollPeriodForm(forms.ModelForm):
    class Meta:
        model = PayrollPeriod
        fields = ["frequency", "start_date", "end_date", "pay_date"]
        widgets = {"start_date": DateInput(), "end_date": DateInput(), "pay_date": DateInput()}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("start_date") and cleaned.get("end_date") and cleaned["end_date"] < cleaned["start_date"]:
            self.add_error("end_date", "End date must be on or after start date.")
        return cleaned


class DeductionsForm(forms.Form):
    paye = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    usc = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    prsi = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    other_deductions = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0)


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "address", "currency", "default_payroll_frequency"]
        widgets = {"address": forms.Textarea(attrs={"rows": 4})}

