"""
Class-Based Views for Assignments: Academic Integrity
PR #46: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from assignments.models_assignments_plagiarism import AssignmentsPlagiarismMaster, AssignmentsPlagiarismConfiguration, AssignmentsPlagiarismAuditTransaction
from assignments.forms_assignments_plagiarism import AssignmentsPlagiarismMasterForm, AssignmentsPlagiarismSearchFilterForm, AssignmentsPlagiarismBatchActionForm
from assignments.services_assignments_plagiarism import AssignmentsPlagiarismWorkflowService, AssignmentsPlagiarismAuditReportingService

class AssignmentsPlagiarismListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AssignmentsPlagiarismMaster
    template_name = "assignments/assignments_plagiarism_list.html"
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
        ctx["filter_form"] = AssignmentsPlagiarismSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AssignmentsPlagiarismBatchActionForm()
        ctx["kpis"] = AssignmentsPlagiarismWorkflowService.calculate_domain_kpis()
        return ctx

class AssignmentsPlagiarismDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AssignmentsPlagiarismMaster
    template_name = "assignments/assignments_plagiarism_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AssignmentsPlagiarismAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AssignmentsPlagiarismAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AssignmentsPlagiarismCreateView(CreateView):
    """Handles controlled creation of new AssignmentsPlagiarismMaster records."""
    model = AssignmentsPlagiarismMaster
    form_class = AssignmentsPlagiarismMasterForm
    template_name = "assignments/assignments_plagiarism_form.html"
    success_url = reverse_lazy("assignments:assignments_plagiarism_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AssignmentsPlagiarism '{self.object.code}' created successfully.")
        return response

class AssignmentsPlagiarismUpdateView(UpdateView):
    """Handles updates and edits to existing AssignmentsPlagiarismMaster records."""
    model = AssignmentsPlagiarismMaster
    form_class = AssignmentsPlagiarismMasterForm
    template_name = "assignments/assignments_plagiarism_form.html"
    success_url = reverse_lazy("assignments:assignments_plagiarism_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AssignmentsPlagiarism '{self.object.code}' updated successfully.")
        return response

class AssignmentsPlagiarismDeleteView(DeleteView):
    """Handles controlled removal of AssignmentsPlagiarismMaster records."""
    model = AssignmentsPlagiarismMaster
    template_name = "assignments/assignments_plagiarism_confirm_delete.html"
    success_url = reverse_lazy("assignments:assignments_plagiarism_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AssignmentsPlagiarism '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AssignmentsPlagiarismPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AssignmentsPlagiarismMaster
    template_name = "assignments/assignments_plagiarism_print.html"
    context_object_name = "record"

class AssignmentsPlagiarismAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "assignments/assignments_plagiarism_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AssignmentsPlagiarismWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AssignmentsPlagiarismMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_assignments_plagiarism_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="assignments_plagiarism_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AssignmentsPlagiarismMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_assignments_plagiarism_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AssignmentsPlagiarismMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
