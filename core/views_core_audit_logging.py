"""
Class-Based Views for Core: Security Audit Trail
PR #92: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from core.models_core_audit_logging import CoreAuditLoggingMaster, CoreAuditLoggingConfiguration, CoreAuditLoggingAuditTransaction
from core.forms_core_audit_logging import CoreAuditLoggingMasterForm, CoreAuditLoggingSearchFilterForm, CoreAuditLoggingBatchActionForm
from core.services_core_audit_logging import CoreAuditLoggingWorkflowService, CoreAuditLoggingAuditReportingService

class CoreAuditLoggingListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = CoreAuditLoggingMaster
    template_name = "core/core_audit_logging_list.html"
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
        ctx["filter_form"] = CoreAuditLoggingSearchFilterForm(self.request.GET)
        ctx["batch_form"] = CoreAuditLoggingBatchActionForm()
        ctx["kpis"] = CoreAuditLoggingWorkflowService.calculate_domain_kpis()
        return ctx

class CoreAuditLoggingDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = CoreAuditLoggingMaster
    template_name = "core/core_audit_logging_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = CoreAuditLoggingAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = CoreAuditLoggingAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class CoreAuditLoggingCreateView(CreateView):
    """Handles controlled creation of new CoreAuditLoggingMaster records."""
    model = CoreAuditLoggingMaster
    form_class = CoreAuditLoggingMasterForm
    template_name = "core/core_audit_logging_form.html"
    success_url = reverse_lazy("core:core_audit_logging_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"CoreAuditLogging '{self.object.code}' created successfully.")
        return response

class CoreAuditLoggingUpdateView(UpdateView):
    """Handles updates and edits to existing CoreAuditLoggingMaster records."""
    model = CoreAuditLoggingMaster
    form_class = CoreAuditLoggingMasterForm
    template_name = "core/core_audit_logging_form.html"
    success_url = reverse_lazy("core:core_audit_logging_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"CoreAuditLogging '{self.object.code}' updated successfully.")
        return response

class CoreAuditLoggingDeleteView(DeleteView):
    """Handles controlled removal of CoreAuditLoggingMaster records."""
    model = CoreAuditLoggingMaster
    template_name = "core/core_audit_logging_confirm_delete.html"
    success_url = reverse_lazy("core:core_audit_logging_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"CoreAuditLogging '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class CoreAuditLoggingPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = CoreAuditLoggingMaster
    template_name = "core/core_audit_logging_print.html"
    context_object_name = "record"

class CoreAuditLoggingAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "core/core_audit_logging_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = CoreAuditLoggingWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = CoreAuditLoggingMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_core_audit_logging_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="core_audit_logging_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in CoreAuditLoggingMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_core_audit_logging_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in CoreAuditLoggingMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
