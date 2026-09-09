"""
Class-Based Views for Enrollment: Cohorts & Sections
PR #30: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from enrollment.models_enrollment_cohorts import EnrollmentCohortsMaster, EnrollmentCohortsConfiguration, EnrollmentCohortsAuditTransaction
from enrollment.forms_enrollment_cohorts import EnrollmentCohortsMasterForm, EnrollmentCohortsSearchFilterForm, EnrollmentCohortsBatchActionForm
from enrollment.services_enrollment_cohorts import EnrollmentCohortsWorkflowService, EnrollmentCohortsAuditReportingService

class EnrollmentCohortsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = EnrollmentCohortsMaster
    template_name = "enrollment/enrollment_cohorts_list.html"
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
        ctx["filter_form"] = EnrollmentCohortsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = EnrollmentCohortsBatchActionForm()
        ctx["kpis"] = EnrollmentCohortsWorkflowService.calculate_domain_kpis()
        return ctx

class EnrollmentCohortsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = EnrollmentCohortsMaster
    template_name = "enrollment/enrollment_cohorts_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = EnrollmentCohortsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = EnrollmentCohortsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class EnrollmentCohortsCreateView(CreateView):
    """Handles controlled creation of new EnrollmentCohortsMaster records."""
    model = EnrollmentCohortsMaster
    form_class = EnrollmentCohortsMasterForm
    template_name = "enrollment/enrollment_cohorts_form.html"
    success_url = reverse_lazy("enrollment:enrollment_cohorts_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"EnrollmentCohorts '{self.object.code}' created successfully.")
        return response

class EnrollmentCohortsUpdateView(UpdateView):
    """Handles updates and edits to existing EnrollmentCohortsMaster records."""
    model = EnrollmentCohortsMaster
    form_class = EnrollmentCohortsMasterForm
    template_name = "enrollment/enrollment_cohorts_form.html"
    success_url = reverse_lazy("enrollment:enrollment_cohorts_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"EnrollmentCohorts '{self.object.code}' updated successfully.")
        return response

class EnrollmentCohortsDeleteView(DeleteView):
    """Handles controlled removal of EnrollmentCohortsMaster records."""
    model = EnrollmentCohortsMaster
    template_name = "enrollment/enrollment_cohorts_confirm_delete.html"
    success_url = reverse_lazy("enrollment:enrollment_cohorts_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"EnrollmentCohorts '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class EnrollmentCohortsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = EnrollmentCohortsMaster
    template_name = "enrollment/enrollment_cohorts_print.html"
    context_object_name = "record"

class EnrollmentCohortsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "enrollment/enrollment_cohorts_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = EnrollmentCohortsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = EnrollmentCohortsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_enrollment_cohorts_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="enrollment_cohorts_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in EnrollmentCohortsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_enrollment_cohorts_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in EnrollmentCohortsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
