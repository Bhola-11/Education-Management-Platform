"""
Class-Based Views for Teachers: Faculty Master Record
PR #21: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from teachers.models_teachers_master_record import TeachersMasterRecordMaster, TeachersMasterRecordConfiguration, TeachersMasterRecordAuditTransaction
from teachers.forms_teachers_master_record import TeachersMasterRecordMasterForm, TeachersMasterRecordSearchFilterForm, TeachersMasterRecordBatchActionForm
from teachers.services_teachers_master_record import TeachersMasterRecordWorkflowService, TeachersMasterRecordAuditReportingService

class TeachersMasterRecordListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = TeachersMasterRecordMaster
    template_name = "teachers/teachers_master_record_list.html"
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
        ctx["filter_form"] = TeachersMasterRecordSearchFilterForm(self.request.GET)
        ctx["batch_form"] = TeachersMasterRecordBatchActionForm()
        ctx["kpis"] = TeachersMasterRecordWorkflowService.calculate_domain_kpis()
        return ctx

class TeachersMasterRecordDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = TeachersMasterRecordMaster
    template_name = "teachers/teachers_master_record_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = TeachersMasterRecordAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = TeachersMasterRecordAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class TeachersMasterRecordCreateView(CreateView):
    """Handles controlled creation of new TeachersMasterRecordMaster records."""
    model = TeachersMasterRecordMaster
    form_class = TeachersMasterRecordMasterForm
    template_name = "teachers/teachers_master_record_form.html"
    success_url = reverse_lazy("teachers:teachers_master_record_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TeachersMasterRecord '{self.object.code}' created successfully.")
        return response

class TeachersMasterRecordUpdateView(UpdateView):
    """Handles updates and edits to existing TeachersMasterRecordMaster records."""
    model = TeachersMasterRecordMaster
    form_class = TeachersMasterRecordMasterForm
    template_name = "teachers/teachers_master_record_form.html"
    success_url = reverse_lazy("teachers:teachers_master_record_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TeachersMasterRecord '{self.object.code}' updated successfully.")
        return response

class TeachersMasterRecordDeleteView(DeleteView):
    """Handles controlled removal of TeachersMasterRecordMaster records."""
    model = TeachersMasterRecordMaster
    template_name = "teachers/teachers_master_record_confirm_delete.html"
    success_url = reverse_lazy("teachers:teachers_master_record_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"TeachersMasterRecord '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class TeachersMasterRecordPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = TeachersMasterRecordMaster
    template_name = "teachers/teachers_master_record_print.html"
    context_object_name = "record"

class TeachersMasterRecordAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "teachers/teachers_master_record_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = TeachersMasterRecordWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = TeachersMasterRecordMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_teachers_master_record_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="teachers_master_record_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in TeachersMasterRecordMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_teachers_master_record_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in TeachersMasterRecordMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
