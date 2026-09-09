"""
Class-Based Views for Notifications: Email Delivery Queue
PR #77: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from notifications.models_notifications_email import NotificationsEmailMaster, NotificationsEmailConfiguration, NotificationsEmailAuditTransaction
from notifications.forms_notifications_email import NotificationsEmailMasterForm, NotificationsEmailSearchFilterForm, NotificationsEmailBatchActionForm
from notifications.services_notifications_email import NotificationsEmailWorkflowService, NotificationsEmailAuditReportingService

class NotificationsEmailListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = NotificationsEmailMaster
    template_name = "notifications/notifications_email_list.html"
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
        ctx["filter_form"] = NotificationsEmailSearchFilterForm(self.request.GET)
        ctx["batch_form"] = NotificationsEmailBatchActionForm()
        ctx["kpis"] = NotificationsEmailWorkflowService.calculate_domain_kpis()
        return ctx

class NotificationsEmailDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = NotificationsEmailMaster
    template_name = "notifications/notifications_email_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = NotificationsEmailAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = NotificationsEmailAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class NotificationsEmailCreateView(CreateView):
    """Handles controlled creation of new NotificationsEmailMaster records."""
    model = NotificationsEmailMaster
    form_class = NotificationsEmailMasterForm
    template_name = "notifications/notifications_email_form.html"
    success_url = reverse_lazy("notifications:notifications_email_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"NotificationsEmail '{self.object.code}' created successfully.")
        return response

class NotificationsEmailUpdateView(UpdateView):
    """Handles updates and edits to existing NotificationsEmailMaster records."""
    model = NotificationsEmailMaster
    form_class = NotificationsEmailMasterForm
    template_name = "notifications/notifications_email_form.html"
    success_url = reverse_lazy("notifications:notifications_email_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"NotificationsEmail '{self.object.code}' updated successfully.")
        return response

class NotificationsEmailDeleteView(DeleteView):
    """Handles controlled removal of NotificationsEmailMaster records."""
    model = NotificationsEmailMaster
    template_name = "notifications/notifications_email_confirm_delete.html"
    success_url = reverse_lazy("notifications:notifications_email_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"NotificationsEmail '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class NotificationsEmailPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = NotificationsEmailMaster
    template_name = "notifications/notifications_email_print.html"
    context_object_name = "record"

class NotificationsEmailAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "notifications/notifications_email_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = NotificationsEmailWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = NotificationsEmailMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_notifications_email_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="notifications_email_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in NotificationsEmailMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_notifications_email_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in NotificationsEmailMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
