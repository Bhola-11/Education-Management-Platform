"""
Class-Based Views for Attendance: Attendance Reporting
PR #41: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from attendance.models_attendance_reports import AttendanceReportsMaster, AttendanceReportsConfiguration, AttendanceReportsAuditTransaction
from attendance.forms_attendance_reports import AttendanceReportsMasterForm, AttendanceReportsSearchFilterForm, AttendanceReportsBatchActionForm
from attendance.services_attendance_reports import AttendanceReportsWorkflowService, AttendanceReportsAuditReportingService

class AttendanceReportsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AttendanceReportsMaster
    template_name = "attendance/attendance_reports_list.html"
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
        ctx["filter_form"] = AttendanceReportsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AttendanceReportsBatchActionForm()
        ctx["kpis"] = AttendanceReportsWorkflowService.calculate_domain_kpis()
        return ctx

class AttendanceReportsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AttendanceReportsMaster
    template_name = "attendance/attendance_reports_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AttendanceReportsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AttendanceReportsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AttendanceReportsCreateView(CreateView):
    """Handles controlled creation of new AttendanceReportsMaster records."""
    model = AttendanceReportsMaster
    form_class = AttendanceReportsMasterForm
    template_name = "attendance/attendance_reports_form.html"
    success_url = reverse_lazy("attendance:attendance_reports_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AttendanceReports '{self.object.code}' created successfully.")
        return response

class AttendanceReportsUpdateView(UpdateView):
    """Handles updates and edits to existing AttendanceReportsMaster records."""
    model = AttendanceReportsMaster
    form_class = AttendanceReportsMasterForm
    template_name = "attendance/attendance_reports_form.html"
    success_url = reverse_lazy("attendance:attendance_reports_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AttendanceReports '{self.object.code}' updated successfully.")
        return response

class AttendanceReportsDeleteView(DeleteView):
    """Handles controlled removal of AttendanceReportsMaster records."""
    model = AttendanceReportsMaster
    template_name = "attendance/attendance_reports_confirm_delete.html"
    success_url = reverse_lazy("attendance:attendance_reports_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AttendanceReports '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AttendanceReportsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AttendanceReportsMaster
    template_name = "attendance/attendance_reports_print.html"
    context_object_name = "record"

class AttendanceReportsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "attendance/attendance_reports_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AttendanceReportsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AttendanceReportsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_attendance_reports_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="attendance_reports_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AttendanceReportsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_attendance_reports_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AttendanceReportsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
