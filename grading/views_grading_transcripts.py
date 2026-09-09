"""
Class-Based Views for Grading: Official Academic Transcripts
PR #56: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from grading.models_grading_transcripts import GradingTranscriptsMaster, GradingTranscriptsConfiguration, GradingTranscriptsAuditTransaction
from grading.forms_grading_transcripts import GradingTranscriptsMasterForm, GradingTranscriptsSearchFilterForm, GradingTranscriptsBatchActionForm
from grading.services_grading_transcripts import GradingTranscriptsWorkflowService, GradingTranscriptsAuditReportingService

class GradingTranscriptsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = GradingTranscriptsMaster
    template_name = "grading/grading_transcripts_list.html"
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
        ctx["filter_form"] = GradingTranscriptsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = GradingTranscriptsBatchActionForm()
        ctx["kpis"] = GradingTranscriptsWorkflowService.calculate_domain_kpis()
        return ctx

class GradingTranscriptsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = GradingTranscriptsMaster
    template_name = "grading/grading_transcripts_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = GradingTranscriptsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = GradingTranscriptsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class GradingTranscriptsCreateView(CreateView):
    """Handles controlled creation of new GradingTranscriptsMaster records."""
    model = GradingTranscriptsMaster
    form_class = GradingTranscriptsMasterForm
    template_name = "grading/grading_transcripts_form.html"
    success_url = reverse_lazy("grading:grading_transcripts_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"GradingTranscripts '{self.object.code}' created successfully.")
        return response

class GradingTranscriptsUpdateView(UpdateView):
    """Handles updates and edits to existing GradingTranscriptsMaster records."""
    model = GradingTranscriptsMaster
    form_class = GradingTranscriptsMasterForm
    template_name = "grading/grading_transcripts_form.html"
    success_url = reverse_lazy("grading:grading_transcripts_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"GradingTranscripts '{self.object.code}' updated successfully.")
        return response

class GradingTranscriptsDeleteView(DeleteView):
    """Handles controlled removal of GradingTranscriptsMaster records."""
    model = GradingTranscriptsMaster
    template_name = "grading/grading_transcripts_confirm_delete.html"
    success_url = reverse_lazy("grading:grading_transcripts_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"GradingTranscripts '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class GradingTranscriptsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = GradingTranscriptsMaster
    template_name = "grading/grading_transcripts_print.html"
    context_object_name = "record"

class GradingTranscriptsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "grading/grading_transcripts_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = GradingTranscriptsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = GradingTranscriptsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_grading_transcripts_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="grading_transcripts_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in GradingTranscriptsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_grading_transcripts_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in GradingTranscriptsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
