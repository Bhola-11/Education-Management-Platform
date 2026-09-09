"""
Class-Based Views for Exams: Exam Scheduling
PR #48: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from exams.models_exams_schedules import ExamsSchedulesMaster, ExamsSchedulesConfiguration, ExamsSchedulesAuditTransaction
from exams.forms_exams_schedules import ExamsSchedulesMasterForm, ExamsSchedulesSearchFilterForm, ExamsSchedulesBatchActionForm
from exams.services_exams_schedules import ExamsSchedulesWorkflowService, ExamsSchedulesAuditReportingService

class ExamsSchedulesListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = ExamsSchedulesMaster
    template_name = "exams/exams_schedules_list.html"
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
        ctx["filter_form"] = ExamsSchedulesSearchFilterForm(self.request.GET)
        ctx["batch_form"] = ExamsSchedulesBatchActionForm()
        ctx["kpis"] = ExamsSchedulesWorkflowService.calculate_domain_kpis()
        return ctx

class ExamsSchedulesDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = ExamsSchedulesMaster
    template_name = "exams/exams_schedules_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = ExamsSchedulesAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = ExamsSchedulesAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class ExamsSchedulesCreateView(CreateView):
    """Handles controlled creation of new ExamsSchedulesMaster records."""
    model = ExamsSchedulesMaster
    form_class = ExamsSchedulesMasterForm
    template_name = "exams/exams_schedules_form.html"
    success_url = reverse_lazy("exams:exams_schedules_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"ExamsSchedules '{self.object.code}' created successfully.")
        return response

class ExamsSchedulesUpdateView(UpdateView):
    """Handles updates and edits to existing ExamsSchedulesMaster records."""
    model = ExamsSchedulesMaster
    form_class = ExamsSchedulesMasterForm
    template_name = "exams/exams_schedules_form.html"
    success_url = reverse_lazy("exams:exams_schedules_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"ExamsSchedules '{self.object.code}' updated successfully.")
        return response

class ExamsSchedulesDeleteView(DeleteView):
    """Handles controlled removal of ExamsSchedulesMaster records."""
    model = ExamsSchedulesMaster
    template_name = "exams/exams_schedules_confirm_delete.html"
    success_url = reverse_lazy("exams:exams_schedules_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"ExamsSchedules '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class ExamsSchedulesPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = ExamsSchedulesMaster
    template_name = "exams/exams_schedules_print.html"
    context_object_name = "record"

class ExamsSchedulesAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "exams/exams_schedules_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = ExamsSchedulesWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = ExamsSchedulesMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_exams_schedules_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="exams_schedules_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in ExamsSchedulesMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_exams_schedules_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in ExamsSchedulesMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
