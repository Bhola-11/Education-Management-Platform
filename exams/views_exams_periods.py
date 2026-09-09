"""
Class-Based Views for Exams: Exam Cycles & Series
PR #47: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from exams.models_exams_periods import ExamsPeriodsMaster, ExamsPeriodsConfiguration, ExamsPeriodsAuditTransaction
from exams.forms_exams_periods import ExamsPeriodsMasterForm, ExamsPeriodsSearchFilterForm, ExamsPeriodsBatchActionForm
from exams.services_exams_periods import ExamsPeriodsWorkflowService, ExamsPeriodsAuditReportingService

class ExamsPeriodsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = ExamsPeriodsMaster
    template_name = "exams/exams_periods_list.html"
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
        ctx["filter_form"] = ExamsPeriodsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = ExamsPeriodsBatchActionForm()
        ctx["kpis"] = ExamsPeriodsWorkflowService.calculate_domain_kpis()
        return ctx

class ExamsPeriodsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = ExamsPeriodsMaster
    template_name = "exams/exams_periods_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = ExamsPeriodsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = ExamsPeriodsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class ExamsPeriodsCreateView(CreateView):
    """Handles controlled creation of new ExamsPeriodsMaster records."""
    model = ExamsPeriodsMaster
    form_class = ExamsPeriodsMasterForm
    template_name = "exams/exams_periods_form.html"
    success_url = reverse_lazy("exams:exams_periods_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"ExamsPeriods '{self.object.code}' created successfully.")
        return response

class ExamsPeriodsUpdateView(UpdateView):
    """Handles updates and edits to existing ExamsPeriodsMaster records."""
    model = ExamsPeriodsMaster
    form_class = ExamsPeriodsMasterForm
    template_name = "exams/exams_periods_form.html"
    success_url = reverse_lazy("exams:exams_periods_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"ExamsPeriods '{self.object.code}' updated successfully.")
        return response

class ExamsPeriodsDeleteView(DeleteView):
    """Handles controlled removal of ExamsPeriodsMaster records."""
    model = ExamsPeriodsMaster
    template_name = "exams/exams_periods_confirm_delete.html"
    success_url = reverse_lazy("exams:exams_periods_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"ExamsPeriods '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class ExamsPeriodsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = ExamsPeriodsMaster
    template_name = "exams/exams_periods_print.html"
    context_object_name = "record"

class ExamsPeriodsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "exams/exams_periods_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = ExamsPeriodsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = ExamsPeriodsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_exams_periods_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="exams_periods_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in ExamsPeriodsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_exams_periods_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in ExamsPeriodsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
