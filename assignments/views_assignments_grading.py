"""
Class-Based Views for Assignments: Assignment Grading
PR #45: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from assignments.models_assignments_grading import AssignmentsGradingMaster, AssignmentsGradingConfiguration, AssignmentsGradingAuditTransaction
from assignments.forms_assignments_grading import AssignmentsGradingMasterForm, AssignmentsGradingSearchFilterForm, AssignmentsGradingBatchActionForm
from assignments.services_assignments_grading import AssignmentsGradingWorkflowService, AssignmentsGradingAuditReportingService

class AssignmentsGradingListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AssignmentsGradingMaster
    template_name = "assignments/assignments_grading_list.html"
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
        ctx["filter_form"] = AssignmentsGradingSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AssignmentsGradingBatchActionForm()
        ctx["kpis"] = AssignmentsGradingWorkflowService.calculate_domain_kpis()
        return ctx

class AssignmentsGradingDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AssignmentsGradingMaster
    template_name = "assignments/assignments_grading_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AssignmentsGradingAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AssignmentsGradingAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AssignmentsGradingCreateView(CreateView):
    """Handles controlled creation of new AssignmentsGradingMaster records."""
    model = AssignmentsGradingMaster
    form_class = AssignmentsGradingMasterForm
    template_name = "assignments/assignments_grading_form.html"
    success_url = reverse_lazy("assignments:assignments_grading_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AssignmentsGrading '{self.object.code}' created successfully.")
        return response

class AssignmentsGradingUpdateView(UpdateView):
    """Handles updates and edits to existing AssignmentsGradingMaster records."""
    model = AssignmentsGradingMaster
    form_class = AssignmentsGradingMasterForm
    template_name = "assignments/assignments_grading_form.html"
    success_url = reverse_lazy("assignments:assignments_grading_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AssignmentsGrading '{self.object.code}' updated successfully.")
        return response

class AssignmentsGradingDeleteView(DeleteView):
    """Handles controlled removal of AssignmentsGradingMaster records."""
    model = AssignmentsGradingMaster
    template_name = "assignments/assignments_grading_confirm_delete.html"
    success_url = reverse_lazy("assignments:assignments_grading_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AssignmentsGrading '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AssignmentsGradingPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AssignmentsGradingMaster
    template_name = "assignments/assignments_grading_print.html"
    context_object_name = "record"

class AssignmentsGradingAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "assignments/assignments_grading_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AssignmentsGradingWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AssignmentsGradingMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_assignments_grading_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="assignments_grading_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AssignmentsGradingMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_assignments_grading_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AssignmentsGradingMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
