"""
Class-Based Views for Certificates: Certificate Template Designer
PR #72: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from certificates.models_certificates_templates import CertificatesTemplatesMaster, CertificatesTemplatesConfiguration, CertificatesTemplatesAuditTransaction
from certificates.forms_certificates_templates import CertificatesTemplatesMasterForm, CertificatesTemplatesSearchFilterForm, CertificatesTemplatesBatchActionForm
from certificates.services_certificates_templates import CertificatesTemplatesWorkflowService, CertificatesTemplatesAuditReportingService

class CertificatesTemplatesListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = CertificatesTemplatesMaster
    template_name = "certificates/certificates_templates_list.html"
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
        ctx["filter_form"] = CertificatesTemplatesSearchFilterForm(self.request.GET)
        ctx["batch_form"] = CertificatesTemplatesBatchActionForm()
        ctx["kpis"] = CertificatesTemplatesWorkflowService.calculate_domain_kpis()
        return ctx

class CertificatesTemplatesDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = CertificatesTemplatesMaster
    template_name = "certificates/certificates_templates_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = CertificatesTemplatesAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = CertificatesTemplatesAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class CertificatesTemplatesCreateView(CreateView):
    """Handles controlled creation of new CertificatesTemplatesMaster records."""
    model = CertificatesTemplatesMaster
    form_class = CertificatesTemplatesMasterForm
    template_name = "certificates/certificates_templates_form.html"
    success_url = reverse_lazy("certificates:certificates_templates_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"CertificatesTemplates '{self.object.code}' created successfully.")
        return response

class CertificatesTemplatesUpdateView(UpdateView):
    """Handles updates and edits to existing CertificatesTemplatesMaster records."""
    model = CertificatesTemplatesMaster
    form_class = CertificatesTemplatesMasterForm
    template_name = "certificates/certificates_templates_form.html"
    success_url = reverse_lazy("certificates:certificates_templates_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"CertificatesTemplates '{self.object.code}' updated successfully.")
        return response

class CertificatesTemplatesDeleteView(DeleteView):
    """Handles controlled removal of CertificatesTemplatesMaster records."""
    model = CertificatesTemplatesMaster
    template_name = "certificates/certificates_templates_confirm_delete.html"
    success_url = reverse_lazy("certificates:certificates_templates_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"CertificatesTemplates '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class CertificatesTemplatesPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = CertificatesTemplatesMaster
    template_name = "certificates/certificates_templates_print.html"
    context_object_name = "record"

class CertificatesTemplatesAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "certificates/certificates_templates_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = CertificatesTemplatesWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = CertificatesTemplatesMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_certificates_templates_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="certificates_templates_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in CertificatesTemplatesMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_certificates_templates_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in CertificatesTemplatesMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
