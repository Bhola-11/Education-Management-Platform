"""
Class-Based Views for Enrollment: Course Registration
PR #28: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from enrollment.models_enrollment_course_reg import EnrollmentCourseRegMaster, EnrollmentCourseRegConfiguration, EnrollmentCourseRegAuditTransaction
from enrollment.forms_enrollment_course_reg import EnrollmentCourseRegMasterForm, EnrollmentCourseRegSearchFilterForm, EnrollmentCourseRegBatchActionForm
from enrollment.services_enrollment_course_reg import EnrollmentCourseRegWorkflowService, EnrollmentCourseRegAuditReportingService

class EnrollmentCourseRegListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = EnrollmentCourseRegMaster
    template_name = "enrollment/enrollment_course_reg_list.html"
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
        ctx["filter_form"] = EnrollmentCourseRegSearchFilterForm(self.request.GET)
        ctx["batch_form"] = EnrollmentCourseRegBatchActionForm()
        ctx["kpis"] = EnrollmentCourseRegWorkflowService.calculate_domain_kpis()
        return ctx

class EnrollmentCourseRegDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = EnrollmentCourseRegMaster
    template_name = "enrollment/enrollment_course_reg_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = EnrollmentCourseRegAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = EnrollmentCourseRegAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class EnrollmentCourseRegCreateView(CreateView):
    """Handles controlled creation of new EnrollmentCourseRegMaster records."""
    model = EnrollmentCourseRegMaster
    form_class = EnrollmentCourseRegMasterForm
    template_name = "enrollment/enrollment_course_reg_form.html"
    success_url = reverse_lazy("enrollment:enrollment_course_reg_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"EnrollmentCourseReg '{self.object.code}' created successfully.")
        return response

class EnrollmentCourseRegUpdateView(UpdateView):
    """Handles updates and edits to existing EnrollmentCourseRegMaster records."""
    model = EnrollmentCourseRegMaster
    form_class = EnrollmentCourseRegMasterForm
    template_name = "enrollment/enrollment_course_reg_form.html"
    success_url = reverse_lazy("enrollment:enrollment_course_reg_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"EnrollmentCourseReg '{self.object.code}' updated successfully.")
        return response

class EnrollmentCourseRegDeleteView(DeleteView):
    """Handles controlled removal of EnrollmentCourseRegMaster records."""
    model = EnrollmentCourseRegMaster
    template_name = "enrollment/enrollment_course_reg_confirm_delete.html"
    success_url = reverse_lazy("enrollment:enrollment_course_reg_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"EnrollmentCourseReg '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class EnrollmentCourseRegPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = EnrollmentCourseRegMaster
    template_name = "enrollment/enrollment_course_reg_print.html"
    context_object_name = "record"

class EnrollmentCourseRegAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "enrollment/enrollment_course_reg_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = EnrollmentCourseRegWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = EnrollmentCourseRegMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_enrollment_course_reg_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="enrollment_course_reg_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in EnrollmentCourseRegMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_enrollment_course_reg_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in EnrollmentCourseRegMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
