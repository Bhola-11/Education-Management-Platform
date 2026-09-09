"""
Class-Based Views for Teachers: Faculty Credentials
PR #22: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from teachers.models_teachers_credentials import TeachersCredentialsMaster, TeachersCredentialsConfiguration, TeachersCredentialsAuditTransaction
from teachers.forms_teachers_credentials import TeachersCredentialsMasterForm, TeachersCredentialsSearchFilterForm, TeachersCredentialsBatchActionForm
from teachers.services_teachers_credentials import TeachersCredentialsWorkflowService, TeachersCredentialsAuditReportingService

class TeachersCredentialsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = TeachersCredentialsMaster
    template_name = "teachers/teachers_credentials_list.html"
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
        ctx["filter_form"] = TeachersCredentialsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = TeachersCredentialsBatchActionForm()
        ctx["kpis"] = TeachersCredentialsWorkflowService.calculate_domain_kpis()
        return ctx

class TeachersCredentialsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = TeachersCredentialsMaster
    template_name = "teachers/teachers_credentials_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = TeachersCredentialsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = TeachersCredentialsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class TeachersCredentialsCreateView(CreateView):
    """Handles controlled creation of new TeachersCredentialsMaster records."""
    model = TeachersCredentialsMaster
    form_class = TeachersCredentialsMasterForm
    template_name = "teachers/teachers_credentials_form.html"
    success_url = reverse_lazy("teachers:teachers_credentials_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TeachersCredentials '{self.object.code}' created successfully.")
        return response

class TeachersCredentialsUpdateView(UpdateView):
    """Handles updates and edits to existing TeachersCredentialsMaster records."""
    model = TeachersCredentialsMaster
    form_class = TeachersCredentialsMasterForm
    template_name = "teachers/teachers_credentials_form.html"
    success_url = reverse_lazy("teachers:teachers_credentials_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TeachersCredentials '{self.object.code}' updated successfully.")
        return response

class TeachersCredentialsDeleteView(DeleteView):
    """Handles controlled removal of TeachersCredentialsMaster records."""
    model = TeachersCredentialsMaster
    template_name = "teachers/teachers_credentials_confirm_delete.html"
    success_url = reverse_lazy("teachers:teachers_credentials_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"TeachersCredentials '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class TeachersCredentialsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = TeachersCredentialsMaster
    template_name = "teachers/teachers_credentials_print.html"
    context_object_name = "record"

class TeachersCredentialsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "teachers/teachers_credentials_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = TeachersCredentialsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = TeachersCredentialsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_teachers_credentials_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="teachers_credentials_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in TeachersCredentialsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_teachers_credentials_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in TeachersCredentialsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
