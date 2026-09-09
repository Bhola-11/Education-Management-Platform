"""
Class-Based Views for Timetables: Schedule Conflict Solver
PR #33: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from timetables.models_timetables_conflict_detector import TimetablesConflictDetectorMaster, TimetablesConflictDetectorConfiguration, TimetablesConflictDetectorAuditTransaction
from timetables.forms_timetables_conflict_detector import TimetablesConflictDetectorMasterForm, TimetablesConflictDetectorSearchFilterForm, TimetablesConflictDetectorBatchActionForm
from timetables.services_timetables_conflict_detector import TimetablesConflictDetectorWorkflowService, TimetablesConflictDetectorAuditReportingService

class TimetablesConflictDetectorListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = TimetablesConflictDetectorMaster
    template_name = "timetables/timetables_conflict_detector_list.html"
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
        ctx["filter_form"] = TimetablesConflictDetectorSearchFilterForm(self.request.GET)
        ctx["batch_form"] = TimetablesConflictDetectorBatchActionForm()
        ctx["kpis"] = TimetablesConflictDetectorWorkflowService.calculate_domain_kpis()
        return ctx

class TimetablesConflictDetectorDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = TimetablesConflictDetectorMaster
    template_name = "timetables/timetables_conflict_detector_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = TimetablesConflictDetectorAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = TimetablesConflictDetectorAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class TimetablesConflictDetectorCreateView(CreateView):
    """Handles controlled creation of new TimetablesConflictDetectorMaster records."""
    model = TimetablesConflictDetectorMaster
    form_class = TimetablesConflictDetectorMasterForm
    template_name = "timetables/timetables_conflict_detector_form.html"
    success_url = reverse_lazy("timetables:timetables_conflict_detector_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TimetablesConflictDetector '{self.object.code}' created successfully.")
        return response

class TimetablesConflictDetectorUpdateView(UpdateView):
    """Handles updates and edits to existing TimetablesConflictDetectorMaster records."""
    model = TimetablesConflictDetectorMaster
    form_class = TimetablesConflictDetectorMasterForm
    template_name = "timetables/timetables_conflict_detector_form.html"
    success_url = reverse_lazy("timetables:timetables_conflict_detector_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TimetablesConflictDetector '{self.object.code}' updated successfully.")
        return response

class TimetablesConflictDetectorDeleteView(DeleteView):
    """Handles controlled removal of TimetablesConflictDetectorMaster records."""
    model = TimetablesConflictDetectorMaster
    template_name = "timetables/timetables_conflict_detector_confirm_delete.html"
    success_url = reverse_lazy("timetables:timetables_conflict_detector_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"TimetablesConflictDetector '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class TimetablesConflictDetectorPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = TimetablesConflictDetectorMaster
    template_name = "timetables/timetables_conflict_detector_print.html"
    context_object_name = "record"

class TimetablesConflictDetectorAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "timetables/timetables_conflict_detector_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = TimetablesConflictDetectorWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = TimetablesConflictDetectorMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_timetables_conflict_detector_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="timetables_conflict_detector_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in TimetablesConflictDetectorMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_timetables_conflict_detector_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in TimetablesConflictDetectorMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
