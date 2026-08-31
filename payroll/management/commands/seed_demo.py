import os
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from payroll.models import Company, Employee, PayrollPeriod, Project, TimesheetEntry
from payroll.services import create_payroll_period, finalise_payroll, review_payroll, update_deductions


EMPLOYEES = [
    ("ENG-001", "Aoife Brennan", "aoife.brennan@example.ie", "HOURLY", "24.50"),
    ("ENG-002", "Cian Murphy", "cian.murphy@example.ie", "HOURLY", "22.00"),
    ("ENG-003", "Niamh O'Connor", "niamh.oconnor@example.ie", "HOURLY", "26.75"),
    ("ENG-004", "Darragh Kelly", "darragh.kelly@example.ie", "HOURLY", "21.50"),
    ("ENG-005", "Saoirse Byrne", "saoirse.byrne@example.ie", "HOURLY", "25.00"),
    ("ENG-006", "Eoin Walsh", "eoin.walsh@example.ie", "MONTHLY", "4800.00"),
    ("ENG-007", "Orla Ryan", "orla.ryan@example.ie", "MONTHLY", "5200.00"),
]
PROJECTS = [
    ("Harbour Quay Retrofit", "Atlantic Property Group", "Dublin 2"),
    ("Liffey Bridge Survey", "Dublin Civil Works", "Dublin 8"),
    ("Cork Innovation Campus", "Munster Developments", "Cork City"),
    ("Galway Water Upgrade", "West Utilities", "Galway City"),
    ("Kilkenny Civic Centre", "Kilkenny Council", "Kilkenny"),
    ("Sligo Coastal Works", "Northwest Infrastructure", "Sligo"),
    ("Limerick Logistics Hub", "Shannon Commercial", "Limerick"),
]


class Command(BaseCommand):
    help = "Create idempotent, entirely fictitious development data."

    def handle(self, *args, **options):
        password = os.getenv("SEED_ADMIN_PASSWORD", "")
        if len(password) < 12:
            raise CommandError("SEED_ADMIN_PASSWORD must contain at least 12 characters.")
        company, _ = Company.objects.update_or_create(pk=1, defaults={"name": "Northstar Engineering Services", "address": "14 Harbour View\nDublin 2\nIreland", "currency": "EUR", "default_payroll_frequency": "WEEKLY"})
        username = os.getenv("SEED_ADMIN_USERNAME", "admin")
        user, _ = get_user_model().objects.get_or_create(username=username, defaults={"email": os.getenv("SEED_ADMIN_EMAIL", "admin@example.ie"), "is_staff": True, "is_superuser": True})
        user.email = os.getenv("SEED_ADMIN_EMAIL", "admin@example.ie"); user.is_staff = True; user.is_superuser = True; user.set_password(password); user.save()

        employees = []
        for number, name, email, payment_type, amount in EMPLOYEES:
            employee, _ = Employee.objects.update_or_create(employee_id=number, defaults={"company": company, "full_name": name, "email": email, "payment_type": payment_type, "hourly_rate": Decimal(amount) if payment_type == "HOURLY" else None, "monthly_salary": Decimal(amount) if payment_type == "MONTHLY" else None, "start_date": date(2025, 1, 6), "status": "ACTIVE"})
            employees.append(employee)
        projects = []
        for name, client, location in PROJECTS:
            project, _ = Project.objects.update_or_create(company=company, name=name, defaults={"client": client, "location": location, "start_date": date(2026, 2, 2), "status": "ACTIVE", "notes": "Fictitious demonstration project."})
            projects.append(project)
        for index, employee in enumerate(employees):
            assigned = [projects[index % 7], projects[(index + 1) % 7]]; employee.projects.set(assigned)
            for day in range(24, 29):
                for project in assigned:
                    TimesheetEntry.objects.update_or_create(employee=employee, project=project, date=date(2026, 8, day), defaults={"hours": Decimal("4.00")})

        period = PayrollPeriod.objects.filter(company=company, frequency="MONTHLY", start_date=date(2026, 8, 1), end_date=date(2026, 8, 31)).first()
        if not period:
            period = create_payroll_period(company=company, frequency="MONTHLY", start_date=date(2026, 8, 1), end_date=date(2026, 8, 31), pay_date=date(2026, 8, 31))
        if period.status != PayrollPeriod.Status.FINALISED:
            for entry in period.entries.all():
                update_deductions(entry_id=entry.pk, paye=entry.gross_pay * Decimal("0.12"), usc=entry.gross_pay * Decimal("0.03"), prsi=entry.gross_pay * Decimal("0.04"), other_deductions=0)
            if period.status == PayrollPeriod.Status.DRAFT: review_payroll(period.pk)
            finalise_payroll(period.pk)
        self.stdout.write(self.style.SUCCESS("Seeded 1 company, 7 employees, 7 projects, sample timesheets and 1 finalised payroll."))
        self.stdout.write(f"Development login username: {username}")
