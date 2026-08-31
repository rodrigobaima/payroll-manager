# Payroll Manager

Small, internal payroll MVP for a fictitious Irish engineering office. It manages employees, active projects, weekly time entries, hourly/monthly gross pay, manual payroll deductions, finalisation, history and professional PDF payslips.

> **Tax limitation:** PAYE, USC and PRSI are manually entered in this MVP. This application does not calculate Irish tax liabilities and does not submit payroll information to Revenue.

## Stack

- Python 3.12 and Django 5.2 LTS
- MySQL 8 with Django ORM and migrations
- Django Templates, Django Forms and Django Admin
- Tailwind CSS 4 and HTMX progressive enhancement
- `DecimalField` / Python `Decimal` for all money
- ReportLab for real A4 PDF generation
- pytest and pytest-django

## Architecture

The browser renders server-side Django templates. Views and forms handle HTTP input and server-side validation. Payroll rules live in `payroll/services.py`, outside views/templates. Django ORM persists MySQL records. Django Admin is the authenticated backoffice.

Key folders:

```text
config/                 Django settings and root URLs
payroll/models.py       Relational domain model
payroll/forms.py        Server-side form validation
payroll/services.py     Gross, deductions, net and workflow rules
payroll/views.py        Authenticated web flows
payroll/pdf.py          A4 payslip generation
payroll/migrations/     MySQL schema migrations
payroll/management/     Fictitious development seed
templates/              English server-rendered UI
static/src/input.css    Tailwind source
static/css/app.css      Compiled CSS
```

## Requirements

- Windows PowerShell
- Python 3.12+
- Node.js 20+ (only to rebuild CSS)
- MySQL 8.0+

## MySQL setup

Sign in to MySQL as an administrator and run:

```sql
CREATE DATABASE payroll_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'payroll_user'@'localhost' IDENTIFIED BY 'choose-a-strong-local-password';
GRANT ALL PRIVILEGES ON payroll_manager.* TO 'payroll_user'@'localhost';
FLUSH PRIVILEGES;
```

For pytest, the same user needs permission to create the temporary `test_payroll_manager` database. Granting privileges on `payroll_manager.*` alone may not be enough; use a dedicated local test user or grant the required test database privileges.

## Installation (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm install
npm run css:build
Copy-Item .env.example .env
```

Edit `.env` and set real local values. Never commit it.

```dotenv
DJANGO_SECRET_KEY="a-long-random-secret"
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
MYSQL_DATABASE=payroll_manager
MYSQL_USER=payroll_user
MYSQL_PASSWORD=your-local-password
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
TIME_ZONE=Europe/Dublin
SEED_ADMIN_USERNAME=admin
SEED_ADMIN_EMAIL=admin@example.ie
SEED_ADMIN_PASSWORD=a-local-password-of-at-least-12-characters
```

Generate a secret without saving it in shell history:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Database, seed and login

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
```

The idempotent seed creates one fictitious company, seven fictitious employees (five hourly, two monthly), seven projects, sample time entries, one finalised payroll and a Django superuser. The username comes from `SEED_ADMIN_USERNAME`; the password comes only from `SEED_ADMIN_PASSWORD` and is hashed by Django.

## Run

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Open `http://127.0.0.1:8000/`. Django Admin is at `http://127.0.0.1:8000/admin/`.

For CSS development, run this in a second terminal:

```powershell
npm run css:watch
```

## Validation

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe -m pytest
npm run css:build
```

Tests cover the exact €800 / €157 / €643 hourly example, monthly gross independent of hours, multiple-project hour aggregation, decimal hours, invalid and negative inputs, excessive deductions and immutable finalised payroll.

## Payroll workflow

1. Record project time.
2. Create a weekly or monthly payroll period.
3. Hourly gross is `hours × hourly rate`; monthly gross is the fixed monthly salary.
4. Enter PAYE, USC, PRSI and other deductions manually.
5. Mark the payroll reviewed and inspect its summary.
6. Finalise explicitly. Entries become immutable and payslips become available.
7. Preview or download the generated PDF.

## Security

- All application pages require Django authentication; there is no public registration.
- CSRF middleware protects every write form.
- Passwords use Django's password hashing.
- Session cookies are HTTP-only and become secure when `DEBUG=False`.
- Secrets and MySQL credentials come from environment variables.
- Salary inputs are validated server-side; database constraints provide a second line of defence.
- PPS numbers and bank details are intentionally not stored.

## Limitations

- No Irish tax engine, Revenue/ROS/RPN integration or tax submission.
- No overtime, leave, benefits, banking, accounting, RBAC or public signup.
- Payslips are generated on demand; PDF bytes are not retained in the database.
- Reopening finalised payroll is intentionally not implemented.
- Deployment configuration is deferred; production requires HTTPS, `DEBUG=False`, secure secrets, backups and a managed MySQL service.
