"""
Class-Based Views for Dashboards: Executive Dashboard
PR #80: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from dashboards.models_dashboards_admin import DashboardsAdminMaster, DashboardsAdminConfiguration, DashboardsAdminAuditTransaction
from dashboards.forms_dashboards_admin import DashboardsAdminMasterForm, DashboardsAdminSearchFilterForm, DashboardsAdminBatchActionForm
from dashboards.services_dashboards_admin import DashboardsAdminWorkflowService, DashboardsAdminAuditReportingService

class DashboardsAdminListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = DashboardsAdminMaster
    template_name = "dashboards/dashboards_admin_list.html"
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
        ctx["filter_form"] = DashboardsAdminSearchFilterForm(self.request.GET)
        ctx["batch_form"] = DashboardsAdminBatchActionForm()
        ctx["kpis"] = DashboardsAdminWorkflowService.calculate_domain_kpis()
        return ctx

class DashboardsAdminDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = DashboardsAdminMaster
    template_name = "dashboards/dashboards_admin_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = DashboardsAdminAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = DashboardsAdminAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class DashboardsAdminCreateView(CreateView):
    """Handles controlled creation of new DashboardsAdminMaster records."""
    model = DashboardsAdminMaster
    form_class = DashboardsAdminMasterForm
    template_name = "dashboards/dashboards_admin_form.html"
    success_url = reverse_lazy("dashboards:dashboards_admin_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"DashboardsAdmin '{self.object.code}' created successfully.")
        return response

class DashboardsAdminUpdateView(UpdateView):
    """Handles updates and edits to existing DashboardsAdminMaster records."""
    model = DashboardsAdminMaster
    form_class = DashboardsAdminMasterForm
    template_name = "dashboards/dashboards_admin_form.html"
    success_url = reverse_lazy("dashboards:dashboards_admin_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"DashboardsAdmin '{self.object.code}' updated successfully.")
        return response

class DashboardsAdminDeleteView(DeleteView):
    """Handles controlled removal of DashboardsAdminMaster records."""
    model = DashboardsAdminMaster
    template_name = "dashboards/dashboards_admin_confirm_delete.html"
    success_url = reverse_lazy("dashboards:dashboards_admin_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"DashboardsAdmin '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class DashboardsAdminPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = DashboardsAdminMaster
    template_name = "dashboards/dashboards_admin_print.html"
    context_object_name = "record"

class DashboardsAdminAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "dashboards/dashboards_admin_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = DashboardsAdminWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = DashboardsAdminMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_dashboards_admin_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="dashboards_admin_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in DashboardsAdminMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_dashboards_admin_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in DashboardsAdminMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
