"""
Class-Based Views for Enrollment: Prerequisite Enforcement
PR #29: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from enrollment.models_enrollment_prereq_check import EnrollmentPrereqCheckMaster, EnrollmentPrereqCheckConfiguration, EnrollmentPrereqCheckAuditTransaction
from enrollment.forms_enrollment_prereq_check import EnrollmentPrereqCheckMasterForm, EnrollmentPrereqCheckSearchFilterForm, EnrollmentPrereqCheckBatchActionForm
from enrollment.services_enrollment_prereq_check import EnrollmentPrereqCheckWorkflowService, EnrollmentPrereqCheckAuditReportingService

class EnrollmentPrereqCheckListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = EnrollmentPrereqCheckMaster
    template_name = "enrollment/enrollment_prereq_check_list.html"
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
        ctx["filter_form"] = EnrollmentPrereqCheckSearchFilterForm(self.request.GET)
        ctx["batch_form"] = EnrollmentPrereqCheckBatchActionForm()
        ctx["kpis"] = EnrollmentPrereqCheckWorkflowService.calculate_domain_kpis()
        return ctx

class EnrollmentPrereqCheckDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = EnrollmentPrereqCheckMaster
    template_name = "enrollment/enrollment_prereq_check_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = EnrollmentPrereqCheckAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = EnrollmentPrereqCheckAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class EnrollmentPrereqCheckCreateView(CreateView):
    """Handles controlled creation of new EnrollmentPrereqCheckMaster records."""
    model = EnrollmentPrereqCheckMaster
    form_class = EnrollmentPrereqCheckMasterForm
    template_name = "enrollment/enrollment_prereq_check_form.html"
    success_url = reverse_lazy("enrollment:enrollment_prereq_check_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"EnrollmentPrereqCheck '{self.object.code}' created successfully.")
        return response

class EnrollmentPrereqCheckUpdateView(UpdateView):
    """Handles updates and edits to existing EnrollmentPrereqCheckMaster records."""
    model = EnrollmentPrereqCheckMaster
    form_class = EnrollmentPrereqCheckMasterForm
    template_name = "enrollment/enrollment_prereq_check_form.html"
    success_url = reverse_lazy("enrollment:enrollment_prereq_check_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"EnrollmentPrereqCheck '{self.object.code}' updated successfully.")
        return response

class EnrollmentPrereqCheckDeleteView(DeleteView):
    """Handles controlled removal of EnrollmentPrereqCheckMaster records."""
    model = EnrollmentPrereqCheckMaster
    template_name = "enrollment/enrollment_prereq_check_confirm_delete.html"
    success_url = reverse_lazy("enrollment:enrollment_prereq_check_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"EnrollmentPrereqCheck '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class EnrollmentPrereqCheckPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = EnrollmentPrereqCheckMaster
    template_name = "enrollment/enrollment_prereq_check_print.html"
    context_object_name = "record"

class EnrollmentPrereqCheckAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "enrollment/enrollment_prereq_check_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = EnrollmentPrereqCheckWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = EnrollmentPrereqCheckMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_enrollment_prereq_check_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="enrollment_prereq_check_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in EnrollmentPrereqCheckMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_enrollment_prereq_check_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in EnrollmentPrereqCheckMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
