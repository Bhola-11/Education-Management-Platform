"""
Class-Based Views for Accounts: Authentication Views
PR #6: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from accounts.models_accounts_auth_views import AccountsAuthViewsMaster, AccountsAuthViewsConfiguration, AccountsAuthViewsAuditTransaction
from accounts.forms_accounts_auth_views import AccountsAuthViewsMasterForm, AccountsAuthViewsSearchFilterForm, AccountsAuthViewsBatchActionForm
from accounts.services_accounts_auth_views import AccountsAuthViewsWorkflowService, AccountsAuthViewsAuditReportingService

class AccountsAuthViewsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AccountsAuthViewsMaster
    template_name = "accounts/accounts_auth_views_list.html"
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
        ctx["filter_form"] = AccountsAuthViewsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AccountsAuthViewsBatchActionForm()
        ctx["kpis"] = AccountsAuthViewsWorkflowService.calculate_domain_kpis()
        return ctx

class AccountsAuthViewsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AccountsAuthViewsMaster
    template_name = "accounts/accounts_auth_views_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AccountsAuthViewsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AccountsAuthViewsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AccountsAuthViewsCreateView(CreateView):
    """Handles controlled creation of new AccountsAuthViewsMaster records."""
    model = AccountsAuthViewsMaster
    form_class = AccountsAuthViewsMasterForm
    template_name = "accounts/accounts_auth_views_form.html"
    success_url = reverse_lazy("accounts:accounts_auth_views_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AccountsAuthViews '{self.object.code}' created successfully.")
        return response

class AccountsAuthViewsUpdateView(UpdateView):
    """Handles updates and edits to existing AccountsAuthViewsMaster records."""
    model = AccountsAuthViewsMaster
    form_class = AccountsAuthViewsMasterForm
    template_name = "accounts/accounts_auth_views_form.html"
    success_url = reverse_lazy("accounts:accounts_auth_views_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AccountsAuthViews '{self.object.code}' updated successfully.")
        return response

class AccountsAuthViewsDeleteView(DeleteView):
    """Handles controlled removal of AccountsAuthViewsMaster records."""
    model = AccountsAuthViewsMaster
    template_name = "accounts/accounts_auth_views_confirm_delete.html"
    success_url = reverse_lazy("accounts:accounts_auth_views_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AccountsAuthViews '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AccountsAuthViewsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AccountsAuthViewsMaster
    template_name = "accounts/accounts_auth_views_print.html"
    context_object_name = "record"

class AccountsAuthViewsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "accounts/accounts_auth_views_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AccountsAuthViewsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AccountsAuthViewsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_accounts_auth_views_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="accounts_auth_views_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AccountsAuthViewsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_accounts_auth_views_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AccountsAuthViewsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
