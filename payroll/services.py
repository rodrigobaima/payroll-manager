from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Employee, PayrollEntry, PayrollPeriod, Payslip, TimesheetEntry

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def as_decimal(value, label="Value"):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError(f"{label} must be a valid number.") from exc
    if not result.is_finite():
        raise ValidationError(f"{label} must be finite.")
    return result


def money(value):
    return as_decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def non_negative(value, label):
    result = as_decimal(value, label)
    if result < ZERO:
        raise ValidationError(f"{label} cannot be negative.")
    return result


def calculate_hourly_gross(hours, hourly_rate):
    return money(non_negative(hours, "Hours") * non_negative(hourly_rate, "Hourly rate"))


def calculate_monthly_gross(monthly_salary):
    return money(non_negative(monthly_salary, "Monthly salary"))


@dataclass(frozen=True)
class NetPayResult:
    paye: Decimal
    usc: Decimal
    prsi: Decimal
    other_deductions: Decimal
    total_deductions: Decimal
    net_pay: Decimal


def calculate_net_pay(gross_pay, paye=ZERO, usc=ZERO, prsi=ZERO, other_deductions=ZERO):
    gross = money(non_negative(gross_pay, "Gross pay"))
    values = [money(non_negative(value, label)) for value, label in [
        (paye, "PAYE"), (usc, "USC"), (prsi, "PRSI"), (other_deductions, "Other deductions")
    ]]
    total = money(sum(values, ZERO))
    if total > gross:
        raise ValidationError("Total deductions cannot exceed gross pay.")
    return NetPayResult(*values, total, money(gross - total))


def gross_for_employee(employee, hours):
    if employee.payment_type == Employee.PaymentType.HOURLY:
        return calculate_hourly_gross(hours, employee.hourly_rate)
    return calculate_monthly_gross(employee.monthly_salary)


@transaction.atomic
def create_payroll_period(*, company, frequency, start_date, end_date, pay_date):
    period = PayrollPeriod.objects.create(company=company, frequency=frequency, start_date=start_date, end_date=end_date, pay_date=pay_date)
    employees = Employee.objects.filter(company=company, status=Employee.Status.ACTIVE).order_by("full_name")
    totals = TimesheetEntry.objects.filter(employee__company=company, date__range=(start_date, end_date)).values("employee_id").annotate(total=Sum("hours"))
    hours_by_employee = {row["employee_id"]: row["total"] or ZERO for row in totals}
    entries = []
    for employee in employees:
        hours = hours_by_employee.get(employee.pk, ZERO)
        gross = gross_for_employee(employee, hours)
        entries.append(PayrollEntry(
            period=period, employee=employee, employee_name=employee.full_name, employee_number=employee.employee_id,
            payment_type=employee.payment_type, hours_worked=hours, hourly_rate=employee.hourly_rate,
            monthly_salary=employee.monthly_salary, gross_pay=gross, net_pay=gross,
        ))
    PayrollEntry.objects.bulk_create(entries)
    return period


@transaction.atomic
def update_deductions(*, entry_id, paye, usc, prsi, other_deductions):
    entry = PayrollEntry.objects.select_for_update().select_related("period").get(pk=entry_id)
    if entry.period.status == PayrollPeriod.Status.FINALISED:
        raise ValidationError("Finalised payroll cannot be changed.")
    result = calculate_net_pay(entry.gross_pay, paye, usc, prsi, other_deductions)
    entry.paye, entry.usc, entry.prsi = result.paye, result.usc, result.prsi
    entry.other_deductions = result.other_deductions
    entry.total_deductions, entry.net_pay = result.total_deductions, result.net_pay
    entry.save(update_fields=["paye", "usc", "prsi", "other_deductions", "total_deductions", "net_pay", "updated_at"])
    return entry


@transaction.atomic
def review_payroll(period_id):
    period = PayrollPeriod.objects.select_for_update().get(pk=period_id)
    if period.status != PayrollPeriod.Status.DRAFT:
        raise ValidationError("Only a draft payroll can be reviewed.")
    period.status, period.reviewed_at = PayrollPeriod.Status.REVIEWED, timezone.now()
    period.save(update_fields=["status", "reviewed_at", "updated_at"])
    return period


@transaction.atomic
def finalise_payroll(period_id):
    period = PayrollPeriod.objects.select_for_update().get(pk=period_id)
    if period.status != PayrollPeriod.Status.REVIEWED:
        raise ValidationError("Payroll must be reviewed before it can be finalised.")
    if not period.entries.exists():
        raise ValidationError("Payroll has no entries.")
    period.status, period.finalised_at = PayrollPeriod.Status.FINALISED, timezone.now()
    period.save(update_fields=["status", "finalised_at", "updated_at"])
    Payslip.objects.bulk_create([
        Payslip(payroll_entry=entry, file_name=f"{entry.employee_number}-{period.pay_date:%Y-%m-%d}-payslip.pdf")
        for entry in period.entries.all()
    ], ignore_conflicts=True)
    return period
