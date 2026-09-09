"""
Class-Based Views for Exams: Invigilation Roster
PR #50: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from exams.models_exams_invigilation import ExamsInvigilationMaster, ExamsInvigilationConfiguration, ExamsInvigilationAuditTransaction
from exams.forms_exams_invigilation import ExamsInvigilationMasterForm, ExamsInvigilationSearchFilterForm, ExamsInvigilationBatchActionForm
from exams.services_exams_invigilation import ExamsInvigilationWorkflowService, ExamsInvigilationAuditReportingService

class ExamsInvigilationListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = ExamsInvigilationMaster
    template_name = "exams/exams_invigilation_list.html"
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
        ctx["filter_form"] = ExamsInvigilationSearchFilterForm(self.request.GET)
        ctx["batch_form"] = ExamsInvigilationBatchActionForm()
        ctx["kpis"] = ExamsInvigilationWorkflowService.calculate_domain_kpis()
        return ctx

class ExamsInvigilationDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = ExamsInvigilationMaster
    template_name = "exams/exams_invigilation_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = ExamsInvigilationAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = ExamsInvigilationAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class ExamsInvigilationCreateView(CreateView):
    """Handles controlled creation of new ExamsInvigilationMaster records."""
    model = ExamsInvigilationMaster
    form_class = ExamsInvigilationMasterForm
    template_name = "exams/exams_invigilation_form.html"
    success_url = reverse_lazy("exams:exams_invigilation_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"ExamsInvigilation '{self.object.code}' created successfully.")
        return response

class ExamsInvigilationUpdateView(UpdateView):
    """Handles updates and edits to existing ExamsInvigilationMaster records."""
    model = ExamsInvigilationMaster
    form_class = ExamsInvigilationMasterForm
    template_name = "exams/exams_invigilation_form.html"
    success_url = reverse_lazy("exams:exams_invigilation_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"ExamsInvigilation '{self.object.code}' updated successfully.")
        return response

class ExamsInvigilationDeleteView(DeleteView):
    """Handles controlled removal of ExamsInvigilationMaster records."""
    model = ExamsInvigilationMaster
    template_name = "exams/exams_invigilation_confirm_delete.html"
    success_url = reverse_lazy("exams:exams_invigilation_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"ExamsInvigilation '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class ExamsInvigilationPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = ExamsInvigilationMaster
    template_name = "exams/exams_invigilation_print.html"
    context_object_name = "record"

class ExamsInvigilationAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "exams/exams_invigilation_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = ExamsInvigilationWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = ExamsInvigilationMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_exams_invigilation_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="exams_invigilation_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in ExamsInvigilationMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_exams_invigilation_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in ExamsInvigilationMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
