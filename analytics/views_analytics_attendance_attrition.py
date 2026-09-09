"""
Class-Based Views for Analytics: Attendance Attrition Models
PR #89: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from analytics.models_analytics_attendance_attrition import AnalyticsAttendanceAttritionMaster, AnalyticsAttendanceAttritionConfiguration, AnalyticsAttendanceAttritionAuditTransaction
from analytics.forms_analytics_attendance_attrition import AnalyticsAttendanceAttritionMasterForm, AnalyticsAttendanceAttritionSearchFilterForm, AnalyticsAttendanceAttritionBatchActionForm
from analytics.services_analytics_attendance_attrition import AnalyticsAttendanceAttritionWorkflowService, AnalyticsAttendanceAttritionAuditReportingService

class AnalyticsAttendanceAttritionListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AnalyticsAttendanceAttritionMaster
    template_name = "analytics/analytics_attendance_attrition_list.html"
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
        ctx["filter_form"] = AnalyticsAttendanceAttritionSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AnalyticsAttendanceAttritionBatchActionForm()
        ctx["kpis"] = AnalyticsAttendanceAttritionWorkflowService.calculate_domain_kpis()
        return ctx

class AnalyticsAttendanceAttritionDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AnalyticsAttendanceAttritionMaster
    template_name = "analytics/analytics_attendance_attrition_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AnalyticsAttendanceAttritionAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AnalyticsAttendanceAttritionAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AnalyticsAttendanceAttritionCreateView(CreateView):
    """Handles controlled creation of new AnalyticsAttendanceAttritionMaster records."""
    model = AnalyticsAttendanceAttritionMaster
    form_class = AnalyticsAttendanceAttritionMasterForm
    template_name = "analytics/analytics_attendance_attrition_form.html"
    success_url = reverse_lazy("analytics:analytics_attendance_attrition_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AnalyticsAttendanceAttrition '{self.object.code}' created successfully.")
        return response

class AnalyticsAttendanceAttritionUpdateView(UpdateView):
    """Handles updates and edits to existing AnalyticsAttendanceAttritionMaster records."""
    model = AnalyticsAttendanceAttritionMaster
    form_class = AnalyticsAttendanceAttritionMasterForm
    template_name = "analytics/analytics_attendance_attrition_form.html"
    success_url = reverse_lazy("analytics:analytics_attendance_attrition_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AnalyticsAttendanceAttrition '{self.object.code}' updated successfully.")
        return response

class AnalyticsAttendanceAttritionDeleteView(DeleteView):
    """Handles controlled removal of AnalyticsAttendanceAttritionMaster records."""
    model = AnalyticsAttendanceAttritionMaster
    template_name = "analytics/analytics_attendance_attrition_confirm_delete.html"
    success_url = reverse_lazy("analytics:analytics_attendance_attrition_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AnalyticsAttendanceAttrition '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AnalyticsAttendanceAttritionPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AnalyticsAttendanceAttritionMaster
    template_name = "analytics/analytics_attendance_attrition_print.html"
    context_object_name = "record"

class AnalyticsAttendanceAttritionAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "analytics/analytics_attendance_attrition_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AnalyticsAttendanceAttritionWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AnalyticsAttendanceAttritionMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_analytics_attendance_attrition_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="analytics_attendance_attrition_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AnalyticsAttendanceAttritionMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_analytics_attendance_attrition_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AnalyticsAttendanceAttritionMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
