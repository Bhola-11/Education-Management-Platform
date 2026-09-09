"""
Class-Based Views for Analytics: Enterprise Export Pipeline
PR #90: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from analytics.models_analytics_export_pipeline import AnalyticsExportPipelineMaster, AnalyticsExportPipelineConfiguration, AnalyticsExportPipelineAuditTransaction
from analytics.forms_analytics_export_pipeline import AnalyticsExportPipelineMasterForm, AnalyticsExportPipelineSearchFilterForm, AnalyticsExportPipelineBatchActionForm
from analytics.services_analytics_export_pipeline import AnalyticsExportPipelineWorkflowService, AnalyticsExportPipelineAuditReportingService

class AnalyticsExportPipelineListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AnalyticsExportPipelineMaster
    template_name = "analytics/analytics_export_pipeline_list.html"
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
        ctx["filter_form"] = AnalyticsExportPipelineSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AnalyticsExportPipelineBatchActionForm()
        ctx["kpis"] = AnalyticsExportPipelineWorkflowService.calculate_domain_kpis()
        return ctx

class AnalyticsExportPipelineDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AnalyticsExportPipelineMaster
    template_name = "analytics/analytics_export_pipeline_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AnalyticsExportPipelineAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AnalyticsExportPipelineAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AnalyticsExportPipelineCreateView(CreateView):
    """Handles controlled creation of new AnalyticsExportPipelineMaster records."""
    model = AnalyticsExportPipelineMaster
    form_class = AnalyticsExportPipelineMasterForm
    template_name = "analytics/analytics_export_pipeline_form.html"
    success_url = reverse_lazy("analytics:analytics_export_pipeline_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AnalyticsExportPipeline '{self.object.code}' created successfully.")
        return response

class AnalyticsExportPipelineUpdateView(UpdateView):
    """Handles updates and edits to existing AnalyticsExportPipelineMaster records."""
    model = AnalyticsExportPipelineMaster
    form_class = AnalyticsExportPipelineMasterForm
    template_name = "analytics/analytics_export_pipeline_form.html"
    success_url = reverse_lazy("analytics:analytics_export_pipeline_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AnalyticsExportPipeline '{self.object.code}' updated successfully.")
        return response

class AnalyticsExportPipelineDeleteView(DeleteView):
    """Handles controlled removal of AnalyticsExportPipelineMaster records."""
    model = AnalyticsExportPipelineMaster
    template_name = "analytics/analytics_export_pipeline_confirm_delete.html"
    success_url = reverse_lazy("analytics:analytics_export_pipeline_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AnalyticsExportPipeline '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AnalyticsExportPipelinePrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AnalyticsExportPipelineMaster
    template_name = "analytics/analytics_export_pipeline_print.html"
    context_object_name = "record"

class AnalyticsExportPipelineAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "analytics/analytics_export_pipeline_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AnalyticsExportPipelineWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AnalyticsExportPipelineMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_analytics_export_pipeline_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="analytics_export_pipeline_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AnalyticsExportPipelineMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_analytics_export_pipeline_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AnalyticsExportPipelineMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
