"""
Class-Based Views for Assignments: Assignment Specifications
PR #42: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from assignments.models_assignments_core import AssignmentsCoreMaster, AssignmentsCoreConfiguration, AssignmentsCoreAuditTransaction
from assignments.forms_assignments_core import AssignmentsCoreMasterForm, AssignmentsCoreSearchFilterForm, AssignmentsCoreBatchActionForm
from assignments.services_assignments_core import AssignmentsCoreWorkflowService, AssignmentsCoreAuditReportingService

class AssignmentsCoreListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AssignmentsCoreMaster
    template_name = "assignments/assignments_core_list.html"
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
        ctx["filter_form"] = AssignmentsCoreSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AssignmentsCoreBatchActionForm()
        ctx["kpis"] = AssignmentsCoreWorkflowService.calculate_domain_kpis()
        return ctx

class AssignmentsCoreDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AssignmentsCoreMaster
    template_name = "assignments/assignments_core_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AssignmentsCoreAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AssignmentsCoreAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AssignmentsCoreCreateView(CreateView):
    """Handles controlled creation of new AssignmentsCoreMaster records."""
    model = AssignmentsCoreMaster
    form_class = AssignmentsCoreMasterForm
    template_name = "assignments/assignments_core_form.html"
    success_url = reverse_lazy("assignments:assignments_core_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AssignmentsCore '{self.object.code}' created successfully.")
        return response

class AssignmentsCoreUpdateView(UpdateView):
    """Handles updates and edits to existing AssignmentsCoreMaster records."""
    model = AssignmentsCoreMaster
    form_class = AssignmentsCoreMasterForm
    template_name = "assignments/assignments_core_form.html"
    success_url = reverse_lazy("assignments:assignments_core_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AssignmentsCore '{self.object.code}' updated successfully.")
        return response

class AssignmentsCoreDeleteView(DeleteView):
    """Handles controlled removal of AssignmentsCoreMaster records."""
    model = AssignmentsCoreMaster
    template_name = "assignments/assignments_core_confirm_delete.html"
    success_url = reverse_lazy("assignments:assignments_core_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AssignmentsCore '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AssignmentsCorePrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AssignmentsCoreMaster
    template_name = "assignments/assignments_core_print.html"
    context_object_name = "record"

class AssignmentsCoreAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "assignments/assignments_core_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AssignmentsCoreWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AssignmentsCoreMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_assignments_core_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="assignments_core_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AssignmentsCoreMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_assignments_core_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AssignmentsCoreMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
