"""
Class-Based Views for Core: Database Diagnostics & Snapshots
PR #93: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from core.models_core_backup_restore import CoreBackupRestoreMaster, CoreBackupRestoreConfiguration, CoreBackupRestoreAuditTransaction
from core.forms_core_backup_restore import CoreBackupRestoreMasterForm, CoreBackupRestoreSearchFilterForm, CoreBackupRestoreBatchActionForm
from core.services_core_backup_restore import CoreBackupRestoreWorkflowService, CoreBackupRestoreAuditReportingService

class CoreBackupRestoreListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = CoreBackupRestoreMaster
    template_name = "core/core_backup_restore_list.html"
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
        ctx["filter_form"] = CoreBackupRestoreSearchFilterForm(self.request.GET)
        ctx["batch_form"] = CoreBackupRestoreBatchActionForm()
        ctx["kpis"] = CoreBackupRestoreWorkflowService.calculate_domain_kpis()
        return ctx

class CoreBackupRestoreDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = CoreBackupRestoreMaster
    template_name = "core/core_backup_restore_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = CoreBackupRestoreAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = CoreBackupRestoreAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class CoreBackupRestoreCreateView(CreateView):
    """Handles controlled creation of new CoreBackupRestoreMaster records."""
    model = CoreBackupRestoreMaster
    form_class = CoreBackupRestoreMasterForm
    template_name = "core/core_backup_restore_form.html"
    success_url = reverse_lazy("core:core_backup_restore_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"CoreBackupRestore '{self.object.code}' created successfully.")
        return response

class CoreBackupRestoreUpdateView(UpdateView):
    """Handles updates and edits to existing CoreBackupRestoreMaster records."""
    model = CoreBackupRestoreMaster
    form_class = CoreBackupRestoreMasterForm
    template_name = "core/core_backup_restore_form.html"
    success_url = reverse_lazy("core:core_backup_restore_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"CoreBackupRestore '{self.object.code}' updated successfully.")
        return response

class CoreBackupRestoreDeleteView(DeleteView):
    """Handles controlled removal of CoreBackupRestoreMaster records."""
    model = CoreBackupRestoreMaster
    template_name = "core/core_backup_restore_confirm_delete.html"
    success_url = reverse_lazy("core:core_backup_restore_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"CoreBackupRestore '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class CoreBackupRestorePrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = CoreBackupRestoreMaster
    template_name = "core/core_backup_restore_print.html"
    context_object_name = "record"

class CoreBackupRestoreAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "core/core_backup_restore_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = CoreBackupRestoreWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = CoreBackupRestoreMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_core_backup_restore_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="core_backup_restore_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in CoreBackupRestoreMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_core_backup_restore_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in CoreBackupRestoreMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
