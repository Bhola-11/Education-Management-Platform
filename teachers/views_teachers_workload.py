"""
Class-Based Views for Teachers: Faculty Workload
PR #24: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from teachers.models_teachers_workload import TeachersWorkloadMaster, TeachersWorkloadConfiguration, TeachersWorkloadAuditTransaction
from teachers.forms_teachers_workload import TeachersWorkloadMasterForm, TeachersWorkloadSearchFilterForm, TeachersWorkloadBatchActionForm
from teachers.services_teachers_workload import TeachersWorkloadWorkflowService, TeachersWorkloadAuditReportingService

class TeachersWorkloadListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = TeachersWorkloadMaster
    template_name = "teachers/teachers_workload_list.html"
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
        ctx["filter_form"] = TeachersWorkloadSearchFilterForm(self.request.GET)
        ctx["batch_form"] = TeachersWorkloadBatchActionForm()
        ctx["kpis"] = TeachersWorkloadWorkflowService.calculate_domain_kpis()
        return ctx

class TeachersWorkloadDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = TeachersWorkloadMaster
    template_name = "teachers/teachers_workload_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = TeachersWorkloadAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = TeachersWorkloadAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class TeachersWorkloadCreateView(CreateView):
    """Handles controlled creation of new TeachersWorkloadMaster records."""
    model = TeachersWorkloadMaster
    form_class = TeachersWorkloadMasterForm
    template_name = "teachers/teachers_workload_form.html"
    success_url = reverse_lazy("teachers:teachers_workload_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TeachersWorkload '{self.object.code}' created successfully.")
        return response

class TeachersWorkloadUpdateView(UpdateView):
    """Handles updates and edits to existing TeachersWorkloadMaster records."""
    model = TeachersWorkloadMaster
    form_class = TeachersWorkloadMasterForm
    template_name = "teachers/teachers_workload_form.html"
    success_url = reverse_lazy("teachers:teachers_workload_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TeachersWorkload '{self.object.code}' updated successfully.")
        return response

class TeachersWorkloadDeleteView(DeleteView):
    """Handles controlled removal of TeachersWorkloadMaster records."""
    model = TeachersWorkloadMaster
    template_name = "teachers/teachers_workload_confirm_delete.html"
    success_url = reverse_lazy("teachers:teachers_workload_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"TeachersWorkload '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class TeachersWorkloadPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = TeachersWorkloadMaster
    template_name = "teachers/teachers_workload_print.html"
    context_object_name = "record"

class TeachersWorkloadAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "teachers/teachers_workload_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = TeachersWorkloadWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = TeachersWorkloadMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_teachers_workload_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="teachers_workload_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in TeachersWorkloadMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_teachers_workload_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in TeachersWorkloadMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
