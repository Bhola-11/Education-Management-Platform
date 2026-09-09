"""
Class-Based Views for Fees: Payment Processing
PR #62: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from fees.models_fees_payments import FeesPaymentsMaster, FeesPaymentsConfiguration, FeesPaymentsAuditTransaction
from fees.forms_fees_payments import FeesPaymentsMasterForm, FeesPaymentsSearchFilterForm, FeesPaymentsBatchActionForm
from fees.services_fees_payments import FeesPaymentsWorkflowService, FeesPaymentsAuditReportingService

class FeesPaymentsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = FeesPaymentsMaster
    template_name = "fees/fees_payments_list.html"
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
        ctx["filter_form"] = FeesPaymentsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = FeesPaymentsBatchActionForm()
        ctx["kpis"] = FeesPaymentsWorkflowService.calculate_domain_kpis()
        return ctx

class FeesPaymentsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = FeesPaymentsMaster
    template_name = "fees/fees_payments_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = FeesPaymentsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = FeesPaymentsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class FeesPaymentsCreateView(CreateView):
    """Handles controlled creation of new FeesPaymentsMaster records."""
    model = FeesPaymentsMaster
    form_class = FeesPaymentsMasterForm
    template_name = "fees/fees_payments_form.html"
    success_url = reverse_lazy("fees:fees_payments_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"FeesPayments '{self.object.code}' created successfully.")
        return response

class FeesPaymentsUpdateView(UpdateView):
    """Handles updates and edits to existing FeesPaymentsMaster records."""
    model = FeesPaymentsMaster
    form_class = FeesPaymentsMasterForm
    template_name = "fees/fees_payments_form.html"
    success_url = reverse_lazy("fees:fees_payments_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"FeesPayments '{self.object.code}' updated successfully.")
        return response

class FeesPaymentsDeleteView(DeleteView):
    """Handles controlled removal of FeesPaymentsMaster records."""
    model = FeesPaymentsMaster
    template_name = "fees/fees_payments_confirm_delete.html"
    success_url = reverse_lazy("fees:fees_payments_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"FeesPayments '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class FeesPaymentsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = FeesPaymentsMaster
    template_name = "fees/fees_payments_print.html"
    context_object_name = "record"

class FeesPaymentsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "fees/fees_payments_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = FeesPaymentsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = FeesPaymentsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_fees_payments_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="fees_payments_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in FeesPaymentsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_fees_payments_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in FeesPaymentsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
