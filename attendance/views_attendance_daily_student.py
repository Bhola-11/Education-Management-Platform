"""
Class-Based Views for Attendance: Daily Student Attendance
PR #36: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from attendance.models_attendance_daily_student import AttendanceDailyStudentMaster, AttendanceDailyStudentConfiguration, AttendanceDailyStudentAuditTransaction
from attendance.forms_attendance_daily_student import AttendanceDailyStudentMasterForm, AttendanceDailyStudentSearchFilterForm, AttendanceDailyStudentBatchActionForm
from attendance.services_attendance_daily_student import AttendanceDailyStudentWorkflowService, AttendanceDailyStudentAuditReportingService

class AttendanceDailyStudentListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AttendanceDailyStudentMaster
    template_name = "attendance/attendance_daily_student_list.html"
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
        ctx["filter_form"] = AttendanceDailyStudentSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AttendanceDailyStudentBatchActionForm()
        ctx["kpis"] = AttendanceDailyStudentWorkflowService.calculate_domain_kpis()
        return ctx

class AttendanceDailyStudentDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AttendanceDailyStudentMaster
    template_name = "attendance/attendance_daily_student_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AttendanceDailyStudentAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AttendanceDailyStudentAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AttendanceDailyStudentCreateView(CreateView):
    """Handles controlled creation of new AttendanceDailyStudentMaster records."""
    model = AttendanceDailyStudentMaster
    form_class = AttendanceDailyStudentMasterForm
    template_name = "attendance/attendance_daily_student_form.html"
    success_url = reverse_lazy("attendance:attendance_daily_student_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AttendanceDailyStudent '{self.object.code}' created successfully.")
        return response

class AttendanceDailyStudentUpdateView(UpdateView):
    """Handles updates and edits to existing AttendanceDailyStudentMaster records."""
    model = AttendanceDailyStudentMaster
    form_class = AttendanceDailyStudentMasterForm
    template_name = "attendance/attendance_daily_student_form.html"
    success_url = reverse_lazy("attendance:attendance_daily_student_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AttendanceDailyStudent '{self.object.code}' updated successfully.")
        return response

class AttendanceDailyStudentDeleteView(DeleteView):
    """Handles controlled removal of AttendanceDailyStudentMaster records."""
    model = AttendanceDailyStudentMaster
    template_name = "attendance/attendance_daily_student_confirm_delete.html"
    success_url = reverse_lazy("attendance:attendance_daily_student_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AttendanceDailyStudent '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AttendanceDailyStudentPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AttendanceDailyStudentMaster
    template_name = "attendance/attendance_daily_student_print.html"
    context_object_name = "record"

class AttendanceDailyStudentAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "attendance/attendance_daily_student_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AttendanceDailyStudentWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AttendanceDailyStudentMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_attendance_daily_student_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="attendance_daily_student_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AttendanceDailyStudentMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_attendance_daily_student_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AttendanceDailyStudentMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
