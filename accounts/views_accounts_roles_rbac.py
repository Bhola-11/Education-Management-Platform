"""
Class-Based Views for Accounts: Role-Based Access Control
PR #4: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from accounts.models_accounts_roles_rbac import AccountsRolesRbacMaster, AccountsRolesRbacConfiguration, AccountsRolesRbacAuditTransaction
from accounts.forms_accounts_roles_rbac import AccountsRolesRbacMasterForm, AccountsRolesRbacSearchFilterForm, AccountsRolesRbacBatchActionForm
from accounts.services_accounts_roles_rbac import AccountsRolesRbacWorkflowService, AccountsRolesRbacAuditReportingService

class AccountsRolesRbacListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AccountsRolesRbacMaster
    template_name = "accounts/accounts_roles_rbac_list.html"
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
        ctx["filter_form"] = AccountsRolesRbacSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AccountsRolesRbacBatchActionForm()
        ctx["kpis"] = AccountsRolesRbacWorkflowService.calculate_domain_kpis()
        return ctx

class AccountsRolesRbacDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AccountsRolesRbacMaster
    template_name = "accounts/accounts_roles_rbac_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AccountsRolesRbacAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AccountsRolesRbacAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AccountsRolesRbacCreateView(CreateView):
    """Handles controlled creation of new AccountsRolesRbacMaster records."""
    model = AccountsRolesRbacMaster
    form_class = AccountsRolesRbacMasterForm
    template_name = "accounts/accounts_roles_rbac_form.html"
    success_url = reverse_lazy("accounts:accounts_roles_rbac_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AccountsRolesRbac '{self.object.code}' created successfully.")
        return response

class AccountsRolesRbacUpdateView(UpdateView):
    """Handles updates and edits to existing AccountsRolesRbacMaster records."""
    model = AccountsRolesRbacMaster
    form_class = AccountsRolesRbacMasterForm
    template_name = "accounts/accounts_roles_rbac_form.html"
    success_url = reverse_lazy("accounts:accounts_roles_rbac_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AccountsRolesRbac '{self.object.code}' updated successfully.")
        return response

class AccountsRolesRbacDeleteView(DeleteView):
    """Handles controlled removal of AccountsRolesRbacMaster records."""
    model = AccountsRolesRbacMaster
    template_name = "accounts/accounts_roles_rbac_confirm_delete.html"
    success_url = reverse_lazy("accounts:accounts_roles_rbac_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AccountsRolesRbac '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AccountsRolesRbacPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AccountsRolesRbacMaster
    template_name = "accounts/accounts_roles_rbac_print.html"
    context_object_name = "record"

class AccountsRolesRbacAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "accounts/accounts_roles_rbac_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AccountsRolesRbacWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AccountsRolesRbacMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_accounts_roles_rbac_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="accounts_roles_rbac_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AccountsRolesRbacMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_accounts_roles_rbac_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AccountsRolesRbacMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
