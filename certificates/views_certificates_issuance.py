"""
Class-Based Views for Certificates: Certificate Issuance Pipeline
PR #73: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from certificates.models_certificates_issuance import CertificatesIssuanceMaster, CertificatesIssuanceConfiguration, CertificatesIssuanceAuditTransaction
from certificates.forms_certificates_issuance import CertificatesIssuanceMasterForm, CertificatesIssuanceSearchFilterForm, CertificatesIssuanceBatchActionForm
from certificates.services_certificates_issuance import CertificatesIssuanceWorkflowService, CertificatesIssuanceAuditReportingService

class CertificatesIssuanceListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = CertificatesIssuanceMaster
    template_name = "certificates/certificates_issuance_list.html"
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
        ctx["filter_form"] = CertificatesIssuanceSearchFilterForm(self.request.GET)
        ctx["batch_form"] = CertificatesIssuanceBatchActionForm()
        ctx["kpis"] = CertificatesIssuanceWorkflowService.calculate_domain_kpis()
        return ctx

class CertificatesIssuanceDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = CertificatesIssuanceMaster
    template_name = "certificates/certificates_issuance_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = CertificatesIssuanceAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = CertificatesIssuanceAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class CertificatesIssuanceCreateView(CreateView):
    """Handles controlled creation of new CertificatesIssuanceMaster records."""
    model = CertificatesIssuanceMaster
    form_class = CertificatesIssuanceMasterForm
    template_name = "certificates/certificates_issuance_form.html"
    success_url = reverse_lazy("certificates:certificates_issuance_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"CertificatesIssuance '{self.object.code}' created successfully.")
        return response

class CertificatesIssuanceUpdateView(UpdateView):
    """Handles updates and edits to existing CertificatesIssuanceMaster records."""
    model = CertificatesIssuanceMaster
    form_class = CertificatesIssuanceMasterForm
    template_name = "certificates/certificates_issuance_form.html"
    success_url = reverse_lazy("certificates:certificates_issuance_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"CertificatesIssuance '{self.object.code}' updated successfully.")
        return response

class CertificatesIssuanceDeleteView(DeleteView):
    """Handles controlled removal of CertificatesIssuanceMaster records."""
    model = CertificatesIssuanceMaster
    template_name = "certificates/certificates_issuance_confirm_delete.html"
    success_url = reverse_lazy("certificates:certificates_issuance_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"CertificatesIssuance '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class CertificatesIssuancePrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = CertificatesIssuanceMaster
    template_name = "certificates/certificates_issuance_print.html"
    context_object_name = "record"

class CertificatesIssuanceAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "certificates/certificates_issuance_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = CertificatesIssuanceWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = CertificatesIssuanceMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_certificates_issuance_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="certificates_issuance_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in CertificatesIssuanceMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_certificates_issuance_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in CertificatesIssuanceMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
