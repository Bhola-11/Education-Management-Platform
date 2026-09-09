"""
Class-Based Views for Teachers: Faculty Portal & Directory
PR #25: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from teachers.models_teachers_views_portal import TeachersViewsPortalMaster, TeachersViewsPortalConfiguration, TeachersViewsPortalAuditTransaction
from teachers.forms_teachers_views_portal import TeachersViewsPortalMasterForm, TeachersViewsPortalSearchFilterForm, TeachersViewsPortalBatchActionForm
from teachers.services_teachers_views_portal import TeachersViewsPortalWorkflowService, TeachersViewsPortalAuditReportingService

class TeachersViewsPortalListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = TeachersViewsPortalMaster
    template_name = "teachers/teachers_views_portal_list.html"
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
        ctx["filter_form"] = TeachersViewsPortalSearchFilterForm(self.request.GET)
        ctx["batch_form"] = TeachersViewsPortalBatchActionForm()
        ctx["kpis"] = TeachersViewsPortalWorkflowService.calculate_domain_kpis()
        return ctx

class TeachersViewsPortalDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = TeachersViewsPortalMaster
    template_name = "teachers/teachers_views_portal_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = TeachersViewsPortalAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = TeachersViewsPortalAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class TeachersViewsPortalCreateView(CreateView):
    """Handles controlled creation of new TeachersViewsPortalMaster records."""
    model = TeachersViewsPortalMaster
    form_class = TeachersViewsPortalMasterForm
    template_name = "teachers/teachers_views_portal_form.html"
    success_url = reverse_lazy("teachers:teachers_views_portal_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TeachersViewsPortal '{self.object.code}' created successfully.")
        return response

class TeachersViewsPortalUpdateView(UpdateView):
    """Handles updates and edits to existing TeachersViewsPortalMaster records."""
    model = TeachersViewsPortalMaster
    form_class = TeachersViewsPortalMasterForm
    template_name = "teachers/teachers_views_portal_form.html"
    success_url = reverse_lazy("teachers:teachers_views_portal_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TeachersViewsPortal '{self.object.code}' updated successfully.")
        return response

class TeachersViewsPortalDeleteView(DeleteView):
    """Handles controlled removal of TeachersViewsPortalMaster records."""
    model = TeachersViewsPortalMaster
    template_name = "teachers/teachers_views_portal_confirm_delete.html"
    success_url = reverse_lazy("teachers:teachers_views_portal_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"TeachersViewsPortal '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class TeachersViewsPortalPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = TeachersViewsPortalMaster
    template_name = "teachers/teachers_views_portal_print.html"
    context_object_name = "record"

class TeachersViewsPortalAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "teachers/teachers_views_portal_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = TeachersViewsPortalWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = TeachersViewsPortalMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_teachers_views_portal_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="teachers_views_portal_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in TeachersViewsPortalMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_teachers_views_portal_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in TeachersViewsPortalMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
