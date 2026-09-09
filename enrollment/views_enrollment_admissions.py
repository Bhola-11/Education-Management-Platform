"""
Class-Based Views for Enrollment: Admissions Pipeline
PR #26: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from enrollment.models_enrollment_admissions import EnrollmentAdmissionsMaster, EnrollmentAdmissionsConfiguration, EnrollmentAdmissionsAuditTransaction
from enrollment.forms_enrollment_admissions import EnrollmentAdmissionsMasterForm, EnrollmentAdmissionsSearchFilterForm, EnrollmentAdmissionsBatchActionForm
from enrollment.services_enrollment_admissions import EnrollmentAdmissionsWorkflowService, EnrollmentAdmissionsAuditReportingService

class EnrollmentAdmissionsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = EnrollmentAdmissionsMaster
    template_name = "enrollment/enrollment_admissions_list.html"
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
        ctx["filter_form"] = EnrollmentAdmissionsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = EnrollmentAdmissionsBatchActionForm()
        ctx["kpis"] = EnrollmentAdmissionsWorkflowService.calculate_domain_kpis()
        return ctx

class EnrollmentAdmissionsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = EnrollmentAdmissionsMaster
    template_name = "enrollment/enrollment_admissions_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = EnrollmentAdmissionsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = EnrollmentAdmissionsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class EnrollmentAdmissionsCreateView(CreateView):
    """Handles controlled creation of new EnrollmentAdmissionsMaster records."""
    model = EnrollmentAdmissionsMaster
    form_class = EnrollmentAdmissionsMasterForm
    template_name = "enrollment/enrollment_admissions_form.html"
    success_url = reverse_lazy("enrollment:enrollment_admissions_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"EnrollmentAdmissions '{self.object.code}' created successfully.")
        return response

class EnrollmentAdmissionsUpdateView(UpdateView):
    """Handles updates and edits to existing EnrollmentAdmissionsMaster records."""
    model = EnrollmentAdmissionsMaster
    form_class = EnrollmentAdmissionsMasterForm
    template_name = "enrollment/enrollment_admissions_form.html"
    success_url = reverse_lazy("enrollment:enrollment_admissions_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"EnrollmentAdmissions '{self.object.code}' updated successfully.")
        return response

class EnrollmentAdmissionsDeleteView(DeleteView):
    """Handles controlled removal of EnrollmentAdmissionsMaster records."""
    model = EnrollmentAdmissionsMaster
    template_name = "enrollment/enrollment_admissions_confirm_delete.html"
    success_url = reverse_lazy("enrollment:enrollment_admissions_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"EnrollmentAdmissions '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class EnrollmentAdmissionsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = EnrollmentAdmissionsMaster
    template_name = "enrollment/enrollment_admissions_print.html"
    context_object_name = "record"

class EnrollmentAdmissionsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "enrollment/enrollment_admissions_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = EnrollmentAdmissionsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = EnrollmentAdmissionsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_enrollment_admissions_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="enrollment_admissions_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in EnrollmentAdmissionsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_enrollment_admissions_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in EnrollmentAdmissionsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
