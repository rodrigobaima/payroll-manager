from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from .models import Company, Employee, PayrollEntry, PayrollPeriod, Project, TimesheetEntry
from .services import calculate_hourly_gross, calculate_monthly_gross, calculate_net_pay, create_payroll_period, finalise_payroll, review_payroll, update_deductions


def test_required_hourly_example_is_exact():
    gross = calculate_hourly_gross("40", "20.00")
    result = calculate_net_pay(gross, "100.00", "25.00", "32.00", "0")
    assert gross == Decimal("800.00")
    assert result.total_deductions == Decimal("157.00")
    assert result.net_pay == Decimal("643.00")


def test_decimal_hours_are_precise():
    assert calculate_hourly_gross("7.5", "20") == Decimal("150.00")


@pytest.mark.parametrize("args", [(-1, 20), (1, -20), ("invalid", 20), (None, 20)])
def test_invalid_hourly_values_are_rejected(args):
    with pytest.raises(ValidationError): calculate_hourly_gross(*args)


def test_negative_or_excess_deductions_are_rejected():
    with pytest.raises(ValidationError): calculate_net_pay(100, -1, 0, 0, 0)
    with pytest.raises(ValidationError): calculate_net_pay(100, 101, 0, 0, 0)


@pytest.fixture
def company(db): return Company.objects.create(name="Test Engineering", address="Dublin")


def employee(company, number, payment_type, amount):
    return Employee.objects.create(company=company, full_name=f"Employee {number}", employee_id=number, email=f"{number.lower()}@example.ie", payment_type=payment_type, hourly_rate=amount if payment_type == "HOURLY" else None, monthly_salary=amount if payment_type == "MONTHLY" else None, start_date=date(2026, 1, 1))


@pytest.mark.django_db
def test_multiple_projects_sum_to_40_hours(company):
    worker = employee(company, "E-1", "HOURLY", Decimal("20.00")); a = Project.objects.create(company=company, name="A", client="A", location="Dublin", start_date=date(2026, 1, 1)); b = Project.objects.create(company=company, name="B", client="B", location="Dublin", start_date=date(2026, 1, 1))
    TimesheetEntry.objects.create(employee=worker, project=a, date=date(2026, 8, 1), hours=20); TimesheetEntry.objects.create(employee=worker, project=b, date=date(2026, 8, 2), hours=20)
    period = create_payroll_period(company=company, frequency="WEEKLY", start_date=date(2026, 8, 1), end_date=date(2026, 8, 7), pay_date=date(2026, 8, 8)); entry = period.entries.get()
    assert entry.hours_worked == Decimal("40.00"); assert entry.gross_pay == Decimal("800.00")


@pytest.mark.django_db
def test_monthly_hours_do_not_change_gross(company):
    salaried = employee(company, "E-2", "MONTHLY", Decimal("4000.00")); project = Project.objects.create(company=company, name="A", client="A", location="Dublin", start_date=date(2026, 1, 1)); TimesheetEntry.objects.create(employee=salaried, project=project, date=date(2026, 8, 1), hours=Decimal("7.50"))
    period = create_payroll_period(company=company, frequency="MONTHLY", start_date=date(2026, 8, 1), end_date=date(2026, 8, 31), pay_date=date(2026, 8, 31)); entry = period.entries.get()
    assert entry.hours_worked == Decimal("7.50"); assert entry.gross_pay == calculate_monthly_gross("4000")


@pytest.mark.django_db
def test_finalised_payroll_cannot_be_changed(company):
    worker = employee(company, "E-3", "HOURLY", Decimal("20.00")); period = create_payroll_period(company=company, frequency="WEEKLY", start_date=date(2026, 8, 1), end_date=date(2026, 8, 7), pay_date=date(2026, 8, 8)); review_payroll(period.pk); finalise_payroll(period.pk)
    entry = PayrollEntry.objects.get(period=period, employee=worker)
    with pytest.raises(ValidationError): update_deductions(entry_id=entry.pk, paye=1, usc=0, prsi=0, other_deductions=0)
    entry.gross_pay = 1
    with pytest.raises(ValidationError): entry.save()
