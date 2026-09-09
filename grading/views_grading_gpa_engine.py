"""
Class-Based Views for Grading: GPA/CGPA Calculation
PR #55: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from grading.models_grading_gpa_engine import GradingGpaEngineMaster, GradingGpaEngineConfiguration, GradingGpaEngineAuditTransaction
from grading.forms_grading_gpa_engine import GradingGpaEngineMasterForm, GradingGpaEngineSearchFilterForm, GradingGpaEngineBatchActionForm
from grading.services_grading_gpa_engine import GradingGpaEngineWorkflowService, GradingGpaEngineAuditReportingService

class GradingGpaEngineListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = GradingGpaEngineMaster
    template_name = "grading/grading_gpa_engine_list.html"
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
        ctx["filter_form"] = GradingGpaEngineSearchFilterForm(self.request.GET)
        ctx["batch_form"] = GradingGpaEngineBatchActionForm()
        ctx["kpis"] = GradingGpaEngineWorkflowService.calculate_domain_kpis()
        return ctx

class GradingGpaEngineDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = GradingGpaEngineMaster
    template_name = "grading/grading_gpa_engine_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = GradingGpaEngineAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = GradingGpaEngineAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class GradingGpaEngineCreateView(CreateView):
    """Handles controlled creation of new GradingGpaEngineMaster records."""
    model = GradingGpaEngineMaster
    form_class = GradingGpaEngineMasterForm
    template_name = "grading/grading_gpa_engine_form.html"
    success_url = reverse_lazy("grading:grading_gpa_engine_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"GradingGpaEngine '{self.object.code}' created successfully.")
        return response

class GradingGpaEngineUpdateView(UpdateView):
    """Handles updates and edits to existing GradingGpaEngineMaster records."""
    model = GradingGpaEngineMaster
    form_class = GradingGpaEngineMasterForm
    template_name = "grading/grading_gpa_engine_form.html"
    success_url = reverse_lazy("grading:grading_gpa_engine_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"GradingGpaEngine '{self.object.code}' updated successfully.")
        return response

class GradingGpaEngineDeleteView(DeleteView):
    """Handles controlled removal of GradingGpaEngineMaster records."""
    model = GradingGpaEngineMaster
    template_name = "grading/grading_gpa_engine_confirm_delete.html"
    success_url = reverse_lazy("grading:grading_gpa_engine_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"GradingGpaEngine '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class GradingGpaEnginePrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = GradingGpaEngineMaster
    template_name = "grading/grading_gpa_engine_print.html"
    context_object_name = "record"

class GradingGpaEngineAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "grading/grading_gpa_engine_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = GradingGpaEngineWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = GradingGpaEngineMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_grading_gpa_engine_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="grading_gpa_engine_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in GradingGpaEngineMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_grading_gpa_engine_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in GradingGpaEngineMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
