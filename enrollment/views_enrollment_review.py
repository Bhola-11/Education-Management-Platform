"""
Class-Based Views for Enrollment: Application Decisioning
PR #27: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from enrollment.models_enrollment_review import EnrollmentReviewMaster, EnrollmentReviewConfiguration, EnrollmentReviewAuditTransaction
from enrollment.forms_enrollment_review import EnrollmentReviewMasterForm, EnrollmentReviewSearchFilterForm, EnrollmentReviewBatchActionForm
from enrollment.services_enrollment_review import EnrollmentReviewWorkflowService, EnrollmentReviewAuditReportingService

class EnrollmentReviewListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = EnrollmentReviewMaster
    template_name = "enrollment/enrollment_review_list.html"
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
        ctx["filter_form"] = EnrollmentReviewSearchFilterForm(self.request.GET)
        ctx["batch_form"] = EnrollmentReviewBatchActionForm()
        ctx["kpis"] = EnrollmentReviewWorkflowService.calculate_domain_kpis()
        return ctx

class EnrollmentReviewDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = EnrollmentReviewMaster
    template_name = "enrollment/enrollment_review_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = EnrollmentReviewAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = EnrollmentReviewAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class EnrollmentReviewCreateView(CreateView):
    """Handles controlled creation of new EnrollmentReviewMaster records."""
    model = EnrollmentReviewMaster
    form_class = EnrollmentReviewMasterForm
    template_name = "enrollment/enrollment_review_form.html"
    success_url = reverse_lazy("enrollment:enrollment_review_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"EnrollmentReview '{self.object.code}' created successfully.")
        return response

class EnrollmentReviewUpdateView(UpdateView):
    """Handles updates and edits to existing EnrollmentReviewMaster records."""
    model = EnrollmentReviewMaster
    form_class = EnrollmentReviewMasterForm
    template_name = "enrollment/enrollment_review_form.html"
    success_url = reverse_lazy("enrollment:enrollment_review_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"EnrollmentReview '{self.object.code}' updated successfully.")
        return response

class EnrollmentReviewDeleteView(DeleteView):
    """Handles controlled removal of EnrollmentReviewMaster records."""
    model = EnrollmentReviewMaster
    template_name = "enrollment/enrollment_review_confirm_delete.html"
    success_url = reverse_lazy("enrollment:enrollment_review_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"EnrollmentReview '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class EnrollmentReviewPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = EnrollmentReviewMaster
    template_name = "enrollment/enrollment_review_print.html"
    context_object_name = "record"

class EnrollmentReviewAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "enrollment/enrollment_review_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = EnrollmentReviewWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = EnrollmentReviewMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_enrollment_review_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="enrollment_review_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in EnrollmentReviewMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_enrollment_review_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in EnrollmentReviewMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
