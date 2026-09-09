"""
Class-Based Views for Accounts: Authentication
PR #3: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from accounts.models_accounts_custom_user import AccountsCustomUserMaster, AccountsCustomUserConfiguration, AccountsCustomUserAuditTransaction
from accounts.forms_accounts_custom_user import AccountsCustomUserMasterForm, AccountsCustomUserSearchFilterForm, AccountsCustomUserBatchActionForm
from accounts.services_accounts_custom_user import AccountsCustomUserWorkflowService, AccountsCustomUserAuditReportingService

class AccountsCustomUserListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AccountsCustomUserMaster
    template_name = "accounts/accounts_custom_user_list.html"
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
        ctx["filter_form"] = AccountsCustomUserSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AccountsCustomUserBatchActionForm()
        ctx["kpis"] = AccountsCustomUserWorkflowService.calculate_domain_kpis()
        return ctx

class AccountsCustomUserDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AccountsCustomUserMaster
    template_name = "accounts/accounts_custom_user_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AccountsCustomUserAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AccountsCustomUserAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AccountsCustomUserCreateView(CreateView):
    """Handles controlled creation of new AccountsCustomUserMaster records."""
    model = AccountsCustomUserMaster
    form_class = AccountsCustomUserMasterForm
    template_name = "accounts/accounts_custom_user_form.html"
    success_url = reverse_lazy("accounts:accounts_custom_user_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AccountsCustomUser '{self.object.code}' created successfully.")
        return response

class AccountsCustomUserUpdateView(UpdateView):
    """Handles updates and edits to existing AccountsCustomUserMaster records."""
    model = AccountsCustomUserMaster
    form_class = AccountsCustomUserMasterForm
    template_name = "accounts/accounts_custom_user_form.html"
    success_url = reverse_lazy("accounts:accounts_custom_user_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AccountsCustomUser '{self.object.code}' updated successfully.")
        return response

class AccountsCustomUserDeleteView(DeleteView):
    """Handles controlled removal of AccountsCustomUserMaster records."""
    model = AccountsCustomUserMaster
    template_name = "accounts/accounts_custom_user_confirm_delete.html"
    success_url = reverse_lazy("accounts:accounts_custom_user_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AccountsCustomUser '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AccountsCustomUserPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AccountsCustomUserMaster
    template_name = "accounts/accounts_custom_user_print.html"
    context_object_name = "record"

class AccountsCustomUserAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "accounts/accounts_custom_user_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AccountsCustomUserWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AccountsCustomUserMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_accounts_custom_user_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="accounts_custom_user_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AccountsCustomUserMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_accounts_custom_user_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AccountsCustomUserMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
