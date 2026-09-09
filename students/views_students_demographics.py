"""
Class-Based Views for Students: Student Demographics
PR #16: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from students.models_students_demographics import StudentsDemographicsMaster, StudentsDemographicsConfiguration, StudentsDemographicsAuditTransaction
from students.forms_students_demographics import StudentsDemographicsMasterForm, StudentsDemographicsSearchFilterForm, StudentsDemographicsBatchActionForm
from students.services_students_demographics import StudentsDemographicsWorkflowService, StudentsDemographicsAuditReportingService

class StudentsDemographicsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = StudentsDemographicsMaster
    template_name = "students/students_demographics_list.html"
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
        ctx["filter_form"] = StudentsDemographicsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = StudentsDemographicsBatchActionForm()
        ctx["kpis"] = StudentsDemographicsWorkflowService.calculate_domain_kpis()
        return ctx

class StudentsDemographicsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = StudentsDemographicsMaster
    template_name = "students/students_demographics_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = StudentsDemographicsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = StudentsDemographicsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class StudentsDemographicsCreateView(CreateView):
    """Handles controlled creation of new StudentsDemographicsMaster records."""
    model = StudentsDemographicsMaster
    form_class = StudentsDemographicsMasterForm
    template_name = "students/students_demographics_form.html"
    success_url = reverse_lazy("students:students_demographics_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"StudentsDemographics '{self.object.code}' created successfully.")
        return response

class StudentsDemographicsUpdateView(UpdateView):
    """Handles updates and edits to existing StudentsDemographicsMaster records."""
    model = StudentsDemographicsMaster
    form_class = StudentsDemographicsMasterForm
    template_name = "students/students_demographics_form.html"
    success_url = reverse_lazy("students:students_demographics_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"StudentsDemographics '{self.object.code}' updated successfully.")
        return response

class StudentsDemographicsDeleteView(DeleteView):
    """Handles controlled removal of StudentsDemographicsMaster records."""
    model = StudentsDemographicsMaster
    template_name = "students/students_demographics_confirm_delete.html"
    success_url = reverse_lazy("students:students_demographics_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"StudentsDemographics '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class StudentsDemographicsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = StudentsDemographicsMaster
    template_name = "students/students_demographics_print.html"
    context_object_name = "record"

class StudentsDemographicsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "students/students_demographics_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = StudentsDemographicsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = StudentsDemographicsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_students_demographics_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="students_demographics_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in StudentsDemographicsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_students_demographics_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in StudentsDemographicsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
