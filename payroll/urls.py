from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("employees/", views.employee_list, name="employee-list"),
    path("employees/new/", views.employee_create, name="employee-create"),
    path("employees/<int:pk>/", views.employee_detail, name="employee-detail"),
    path("employees/<int:pk>/edit/", views.employee_edit, name="employee-edit"),
    path("employees/<int:pk>/deactivate/", views.employee_deactivate, name="employee-deactivate"),
    path("projects/", views.project_list, name="project-list"),
    path("projects/new/", views.project_create, name="project-create"),
    path("projects/<int:pk>/", views.project_detail, name="project-detail"),
    path("projects/<int:pk>/edit/", views.project_edit, name="project-edit"),
    path("projects/<int:pk>/complete/", views.project_complete, name="project-complete"),
    path("timesheets/", views.timesheet_list, name="timesheet-list"),
    path("timesheets/<int:pk>/delete/", views.timesheet_delete, name="timesheet-delete"),
    path("payroll/", views.payroll_list, name="payroll-list"),
    path("payroll/new/", views.payroll_create, name="payroll-create"),
    path("payroll/<int:pk>/", views.payroll_detail, name="payroll-detail"),
    path("payroll/<int:pk>/entries/<int:entry_pk>/deductions/", views.payroll_deductions, name="payroll-deductions"),
    path("payroll/<int:pk>/review/", views.payroll_review, name="payroll-review"),
    path("payroll/<int:pk>/finalise/", views.payroll_finalise, name="payroll-finalise"),
    path("payslips/", views.payslip_list, name="payslip-list"),
    path("payslips/<int:entry_pk>/", views.payslip_detail, name="payslip-detail"),
    path("payslips/<int:entry_pk>/pdf/", views.payslip_pdf, name="payslip-pdf"),
    path("settings/", views.settings_view, name="settings"),
]
