"""
Class-Based Views for Students: Student Health & Safety
PR #18: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from students.models_students_emergency_health import StudentsEmergencyHealthMaster, StudentsEmergencyHealthConfiguration, StudentsEmergencyHealthAuditTransaction
from students.forms_students_emergency_health import StudentsEmergencyHealthMasterForm, StudentsEmergencyHealthSearchFilterForm, StudentsEmergencyHealthBatchActionForm
from students.services_students_emergency_health import StudentsEmergencyHealthWorkflowService, StudentsEmergencyHealthAuditReportingService

class StudentsEmergencyHealthListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = StudentsEmergencyHealthMaster
    template_name = "students/students_emergency_health_list.html"
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
        ctx["filter_form"] = StudentsEmergencyHealthSearchFilterForm(self.request.GET)
        ctx["batch_form"] = StudentsEmergencyHealthBatchActionForm()
        ctx["kpis"] = StudentsEmergencyHealthWorkflowService.calculate_domain_kpis()
        return ctx

class StudentsEmergencyHealthDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = StudentsEmergencyHealthMaster
    template_name = "students/students_emergency_health_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = StudentsEmergencyHealthAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = StudentsEmergencyHealthAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class StudentsEmergencyHealthCreateView(CreateView):
    """Handles controlled creation of new StudentsEmergencyHealthMaster records."""
    model = StudentsEmergencyHealthMaster
    form_class = StudentsEmergencyHealthMasterForm
    template_name = "students/students_emergency_health_form.html"
    success_url = reverse_lazy("students:students_emergency_health_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"StudentsEmergencyHealth '{self.object.code}' created successfully.")
        return response

class StudentsEmergencyHealthUpdateView(UpdateView):
    """Handles updates and edits to existing StudentsEmergencyHealthMaster records."""
    model = StudentsEmergencyHealthMaster
    form_class = StudentsEmergencyHealthMasterForm
    template_name = "students/students_emergency_health_form.html"
    success_url = reverse_lazy("students:students_emergency_health_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"StudentsEmergencyHealth '{self.object.code}' updated successfully.")
        return response

class StudentsEmergencyHealthDeleteView(DeleteView):
    """Handles controlled removal of StudentsEmergencyHealthMaster records."""
    model = StudentsEmergencyHealthMaster
    template_name = "students/students_emergency_health_confirm_delete.html"
    success_url = reverse_lazy("students:students_emergency_health_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"StudentsEmergencyHealth '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class StudentsEmergencyHealthPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = StudentsEmergencyHealthMaster
    template_name = "students/students_emergency_health_print.html"
    context_object_name = "record"

class StudentsEmergencyHealthAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "students/students_emergency_health_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = StudentsEmergencyHealthWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = StudentsEmergencyHealthMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_students_emergency_health_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="students_emergency_health_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in StudentsEmergencyHealthMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_students_emergency_health_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in StudentsEmergencyHealthMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
