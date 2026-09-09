"""
Class-Based Views for Fees: Installment Plans
PR #60: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from fees.models_fees_installments import FeesInstallmentsMaster, FeesInstallmentsConfiguration, FeesInstallmentsAuditTransaction
from fees.forms_fees_installments import FeesInstallmentsMasterForm, FeesInstallmentsSearchFilterForm, FeesInstallmentsBatchActionForm
from fees.services_fees_installments import FeesInstallmentsWorkflowService, FeesInstallmentsAuditReportingService

class FeesInstallmentsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = FeesInstallmentsMaster
    template_name = "fees/fees_installments_list.html"
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
        ctx["filter_form"] = FeesInstallmentsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = FeesInstallmentsBatchActionForm()
        ctx["kpis"] = FeesInstallmentsWorkflowService.calculate_domain_kpis()
        return ctx

class FeesInstallmentsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = FeesInstallmentsMaster
    template_name = "fees/fees_installments_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = FeesInstallmentsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = FeesInstallmentsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class FeesInstallmentsCreateView(CreateView):
    """Handles controlled creation of new FeesInstallmentsMaster records."""
    model = FeesInstallmentsMaster
    form_class = FeesInstallmentsMasterForm
    template_name = "fees/fees_installments_form.html"
    success_url = reverse_lazy("fees:fees_installments_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"FeesInstallments '{self.object.code}' created successfully.")
        return response

class FeesInstallmentsUpdateView(UpdateView):
    """Handles updates and edits to existing FeesInstallmentsMaster records."""
    model = FeesInstallmentsMaster
    form_class = FeesInstallmentsMasterForm
    template_name = "fees/fees_installments_form.html"
    success_url = reverse_lazy("fees:fees_installments_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"FeesInstallments '{self.object.code}' updated successfully.")
        return response

class FeesInstallmentsDeleteView(DeleteView):
    """Handles controlled removal of FeesInstallmentsMaster records."""
    model = FeesInstallmentsMaster
    template_name = "fees/fees_installments_confirm_delete.html"
    success_url = reverse_lazy("fees:fees_installments_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"FeesInstallments '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class FeesInstallmentsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = FeesInstallmentsMaster
    template_name = "fees/fees_installments_print.html"
    context_object_name = "record"

class FeesInstallmentsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "fees/fees_installments_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = FeesInstallmentsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = FeesInstallmentsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_fees_installments_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="fees_installments_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in FeesInstallmentsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_fees_installments_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in FeesInstallmentsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
