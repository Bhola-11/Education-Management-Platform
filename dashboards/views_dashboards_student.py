"""
Class-Based Views for Dashboards: Student Self-Service Hub
PR #83: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from dashboards.models_dashboards_student import DashboardsStudentMaster, DashboardsStudentConfiguration, DashboardsStudentAuditTransaction
from dashboards.forms_dashboards_student import DashboardsStudentMasterForm, DashboardsStudentSearchFilterForm, DashboardsStudentBatchActionForm
from dashboards.services_dashboards_student import DashboardsStudentWorkflowService, DashboardsStudentAuditReportingService

class DashboardsStudentListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = DashboardsStudentMaster
    template_name = "dashboards/dashboards_student_list.html"
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
        ctx["filter_form"] = DashboardsStudentSearchFilterForm(self.request.GET)
        ctx["batch_form"] = DashboardsStudentBatchActionForm()
        ctx["kpis"] = DashboardsStudentWorkflowService.calculate_domain_kpis()
        return ctx

class DashboardsStudentDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = DashboardsStudentMaster
    template_name = "dashboards/dashboards_student_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = DashboardsStudentAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = DashboardsStudentAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class DashboardsStudentCreateView(CreateView):
    """Handles controlled creation of new DashboardsStudentMaster records."""
    model = DashboardsStudentMaster
    form_class = DashboardsStudentMasterForm
    template_name = "dashboards/dashboards_student_form.html"
    success_url = reverse_lazy("dashboards:dashboards_student_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"DashboardsStudent '{self.object.code}' created successfully.")
        return response

class DashboardsStudentUpdateView(UpdateView):
    """Handles updates and edits to existing DashboardsStudentMaster records."""
    model = DashboardsStudentMaster
    form_class = DashboardsStudentMasterForm
    template_name = "dashboards/dashboards_student_form.html"
    success_url = reverse_lazy("dashboards:dashboards_student_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"DashboardsStudent '{self.object.code}' updated successfully.")
        return response

class DashboardsStudentDeleteView(DeleteView):
    """Handles controlled removal of DashboardsStudentMaster records."""
    model = DashboardsStudentMaster
    template_name = "dashboards/dashboards_student_confirm_delete.html"
    success_url = reverse_lazy("dashboards:dashboards_student_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"DashboardsStudent '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class DashboardsStudentPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = DashboardsStudentMaster
    template_name = "dashboards/dashboards_student_print.html"
    context_object_name = "record"

class DashboardsStudentAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "dashboards/dashboards_student_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = DashboardsStudentWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = DashboardsStudentMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_dashboards_student_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="dashboards_student_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in DashboardsStudentMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_dashboards_student_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in DashboardsStudentMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
