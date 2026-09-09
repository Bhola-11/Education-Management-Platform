"""
Class-Based Views for Students: Students & Enrollment Tests
PR #96: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from students.models_students_and_enrollment_suite import StudentsAndEnrollmentSuiteMaster, StudentsAndEnrollmentSuiteConfiguration, StudentsAndEnrollmentSuiteAuditTransaction
from students.forms_students_and_enrollment_suite import StudentsAndEnrollmentSuiteMasterForm, StudentsAndEnrollmentSuiteSearchFilterForm, StudentsAndEnrollmentSuiteBatchActionForm
from students.services_students_and_enrollment_suite import StudentsAndEnrollmentSuiteWorkflowService, StudentsAndEnrollmentSuiteAuditReportingService

class StudentsAndEnrollmentSuiteListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = StudentsAndEnrollmentSuiteMaster
    template_name = "students/students_and_enrollment_suite_list.html"
    context_object_name = "records"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        status = self.request.GET.get("status")
        is_active = self.request.GET.get("is_active")

        if q:
            qs = qs.filter(models.Q(code__icontains=q) | models.Q(name__icontains=q))
        if status:
            qs = qs.filter(status=status)
        if is_active in ("1", "0"):
            qs = qs.filter(is_active=(is_active == "1"))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_form"] = StudentsAndEnrollmentSuiteSearchFilterForm(self.request.GET)
        ctx["batch_form"] = StudentsAndEnrollmentSuiteBatchActionForm()
        ctx["kpis"] = StudentsAndEnrollmentSuiteWorkflowService.calculate_domain_kpis()
        return ctx

class StudentsAndEnrollmentSuiteDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = StudentsAndEnrollmentSuiteMaster
    template_name = "students/students_and_enrollment_suite_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = StudentsAndEnrollmentSuiteAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = StudentsAndEnrollmentSuiteAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class StudentsAndEnrollmentSuiteCreateView(CreateView):
    """Handles controlled creation of new StudentsAndEnrollmentSuiteMaster records."""
    model = StudentsAndEnrollmentSuiteMaster
    form_class = StudentsAndEnrollmentSuiteMasterForm
    template_name = "students/students_and_enrollment_suite_form.html"
    success_url = reverse_lazy("students:students_and_enrollment_suite_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"StudentsAndEnrollmentSuite '{self.object.code}' created successfully.")
        return response

class StudentsAndEnrollmentSuiteUpdateView(UpdateView):
    """Handles updates and edits to existing StudentsAndEnrollmentSuiteMaster records."""
    model = StudentsAndEnrollmentSuiteMaster
    form_class = StudentsAndEnrollmentSuiteMasterForm
    template_name = "students/students_and_enrollment_suite_form.html"
    success_url = reverse_lazy("students:students_and_enrollment_suite_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"StudentsAndEnrollmentSuite '{self.object.code}' updated successfully.")
        return response

class StudentsAndEnrollmentSuiteDeleteView(DeleteView):
    """Handles controlled removal of StudentsAndEnrollmentSuiteMaster records."""
    model = StudentsAndEnrollmentSuiteMaster
    template_name = "students/students_and_enrollment_suite_confirm_delete.html"
    success_url = reverse_lazy("students:students_and_enrollment_suite_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"StudentsAndEnrollmentSuite '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class StudentsAndEnrollmentSuitePrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = StudentsAndEnrollmentSuiteMaster
    template_name = "students/students_and_enrollment_suite_print.html"
    context_object_name = "record"

class StudentsAndEnrollmentSuiteAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "students/students_and_enrollment_suite_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = StudentsAndEnrollmentSuiteWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = StudentsAndEnrollmentSuiteMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_students_and_enrollment_suite_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="students_and_enrollment_suite_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in StudentsAndEnrollmentSuiteMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_students_and_enrollment_suite_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in StudentsAndEnrollmentSuiteMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
