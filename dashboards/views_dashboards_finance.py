"""
Class-Based Views for Dashboards: Bursar Financial Hub
PR #85: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from dashboards.models_dashboards_finance import DashboardsFinanceMaster, DashboardsFinanceConfiguration, DashboardsFinanceAuditTransaction
from dashboards.forms_dashboards_finance import DashboardsFinanceMasterForm, DashboardsFinanceSearchFilterForm, DashboardsFinanceBatchActionForm
from dashboards.services_dashboards_finance import DashboardsFinanceWorkflowService, DashboardsFinanceAuditReportingService

class DashboardsFinanceListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = DashboardsFinanceMaster
    template_name = "dashboards/dashboards_finance_list.html"
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
        ctx["filter_form"] = DashboardsFinanceSearchFilterForm(self.request.GET)
        ctx["batch_form"] = DashboardsFinanceBatchActionForm()
        ctx["kpis"] = DashboardsFinanceWorkflowService.calculate_domain_kpis()
        return ctx

class DashboardsFinanceDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = DashboardsFinanceMaster
    template_name = "dashboards/dashboards_finance_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = DashboardsFinanceAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = DashboardsFinanceAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class DashboardsFinanceCreateView(CreateView):
    """Handles controlled creation of new DashboardsFinanceMaster records."""
    model = DashboardsFinanceMaster
    form_class = DashboardsFinanceMasterForm
    template_name = "dashboards/dashboards_finance_form.html"
    success_url = reverse_lazy("dashboards:dashboards_finance_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"DashboardsFinance '{self.object.code}' created successfully.")
        return response

class DashboardsFinanceUpdateView(UpdateView):
    """Handles updates and edits to existing DashboardsFinanceMaster records."""
    model = DashboardsFinanceMaster
    form_class = DashboardsFinanceMasterForm
    template_name = "dashboards/dashboards_finance_form.html"
    success_url = reverse_lazy("dashboards:dashboards_finance_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"DashboardsFinance '{self.object.code}' updated successfully.")
        return response

class DashboardsFinanceDeleteView(DeleteView):
    """Handles controlled removal of DashboardsFinanceMaster records."""
    model = DashboardsFinanceMaster
    template_name = "dashboards/dashboards_finance_confirm_delete.html"
    success_url = reverse_lazy("dashboards:dashboards_finance_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"DashboardsFinance '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class DashboardsFinancePrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = DashboardsFinanceMaster
    template_name = "dashboards/dashboards_finance_print.html"
    context_object_name = "record"

class DashboardsFinanceAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "dashboards/dashboards_finance_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = DashboardsFinanceWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = DashboardsFinanceMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_dashboards_finance_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="dashboards_finance_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in DashboardsFinanceMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_dashboards_finance_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in DashboardsFinanceMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
