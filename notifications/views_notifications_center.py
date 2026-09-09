"""
Class-Based Views for Notifications: Notification Center
PR #76: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from notifications.models_notifications_center import NotificationsCenterMaster, NotificationsCenterConfiguration, NotificationsCenterAuditTransaction
from notifications.forms_notifications_center import NotificationsCenterMasterForm, NotificationsCenterSearchFilterForm, NotificationsCenterBatchActionForm
from notifications.services_notifications_center import NotificationsCenterWorkflowService, NotificationsCenterAuditReportingService

class NotificationsCenterListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = NotificationsCenterMaster
    template_name = "notifications/notifications_center_list.html"
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
        ctx["filter_form"] = NotificationsCenterSearchFilterForm(self.request.GET)
        ctx["batch_form"] = NotificationsCenterBatchActionForm()
        ctx["kpis"] = NotificationsCenterWorkflowService.calculate_domain_kpis()
        return ctx

class NotificationsCenterDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = NotificationsCenterMaster
    template_name = "notifications/notifications_center_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = NotificationsCenterAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = NotificationsCenterAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class NotificationsCenterCreateView(CreateView):
    """Handles controlled creation of new NotificationsCenterMaster records."""
    model = NotificationsCenterMaster
    form_class = NotificationsCenterMasterForm
    template_name = "notifications/notifications_center_form.html"
    success_url = reverse_lazy("notifications:notifications_center_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"NotificationsCenter '{self.object.code}' created successfully.")
        return response

class NotificationsCenterUpdateView(UpdateView):
    """Handles updates and edits to existing NotificationsCenterMaster records."""
    model = NotificationsCenterMaster
    form_class = NotificationsCenterMasterForm
    template_name = "notifications/notifications_center_form.html"
    success_url = reverse_lazy("notifications:notifications_center_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"NotificationsCenter '{self.object.code}' updated successfully.")
        return response

class NotificationsCenterDeleteView(DeleteView):
    """Handles controlled removal of NotificationsCenterMaster records."""
    model = NotificationsCenterMaster
    template_name = "notifications/notifications_center_confirm_delete.html"
    success_url = reverse_lazy("notifications:notifications_center_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"NotificationsCenter '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class NotificationsCenterPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = NotificationsCenterMaster
    template_name = "notifications/notifications_center_print.html"
    context_object_name = "record"

class NotificationsCenterAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "notifications/notifications_center_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = NotificationsCenterWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = NotificationsCenterMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_notifications_center_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="notifications_center_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in NotificationsCenterMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_notifications_center_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in NotificationsCenterMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
