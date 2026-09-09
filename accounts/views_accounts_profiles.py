"""
Class-Based Views for Accounts: User Profiles
PR #5: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from accounts.models_accounts_profiles import AccountsProfilesMaster, AccountsProfilesConfiguration, AccountsProfilesAuditTransaction
from accounts.forms_accounts_profiles import AccountsProfilesMasterForm, AccountsProfilesSearchFilterForm, AccountsProfilesBatchActionForm
from accounts.services_accounts_profiles import AccountsProfilesWorkflowService, AccountsProfilesAuditReportingService

class AccountsProfilesListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AccountsProfilesMaster
    template_name = "accounts/accounts_profiles_list.html"
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
        ctx["filter_form"] = AccountsProfilesSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AccountsProfilesBatchActionForm()
        ctx["kpis"] = AccountsProfilesWorkflowService.calculate_domain_kpis()
        return ctx

class AccountsProfilesDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AccountsProfilesMaster
    template_name = "accounts/accounts_profiles_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AccountsProfilesAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AccountsProfilesAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AccountsProfilesCreateView(CreateView):
    """Handles controlled creation of new AccountsProfilesMaster records."""
    model = AccountsProfilesMaster
    form_class = AccountsProfilesMasterForm
    template_name = "accounts/accounts_profiles_form.html"
    success_url = reverse_lazy("accounts:accounts_profiles_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AccountsProfiles '{self.object.code}' created successfully.")
        return response

class AccountsProfilesUpdateView(UpdateView):
    """Handles updates and edits to existing AccountsProfilesMaster records."""
    model = AccountsProfilesMaster
    form_class = AccountsProfilesMasterForm
    template_name = "accounts/accounts_profiles_form.html"
    success_url = reverse_lazy("accounts:accounts_profiles_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AccountsProfiles '{self.object.code}' updated successfully.")
        return response

class AccountsProfilesDeleteView(DeleteView):
    """Handles controlled removal of AccountsProfilesMaster records."""
    model = AccountsProfilesMaster
    template_name = "accounts/accounts_profiles_confirm_delete.html"
    success_url = reverse_lazy("accounts:accounts_profiles_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AccountsProfiles '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AccountsProfilesPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AccountsProfilesMaster
    template_name = "accounts/accounts_profiles_print.html"
    context_object_name = "record"

class AccountsProfilesAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "accounts/accounts_profiles_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AccountsProfilesWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AccountsProfilesMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_accounts_profiles_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="accounts_profiles_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AccountsProfilesMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_accounts_profiles_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AccountsProfilesMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
