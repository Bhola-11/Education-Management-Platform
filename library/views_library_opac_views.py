"""
Class-Based Views for Library: OPAC Public Catalog
PR #71: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from library.models_library_opac_views import LibraryOpacViewsMaster, LibraryOpacViewsConfiguration, LibraryOpacViewsAuditTransaction
from library.forms_library_opac_views import LibraryOpacViewsMasterForm, LibraryOpacViewsSearchFilterForm, LibraryOpacViewsBatchActionForm
from library.services_library_opac_views import LibraryOpacViewsWorkflowService, LibraryOpacViewsAuditReportingService

class LibraryOpacViewsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = LibraryOpacViewsMaster
    template_name = "library/library_opac_views_list.html"
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
        ctx["filter_form"] = LibraryOpacViewsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = LibraryOpacViewsBatchActionForm()
        ctx["kpis"] = LibraryOpacViewsWorkflowService.calculate_domain_kpis()
        return ctx

class LibraryOpacViewsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = LibraryOpacViewsMaster
    template_name = "library/library_opac_views_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = LibraryOpacViewsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = LibraryOpacViewsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class LibraryOpacViewsCreateView(CreateView):
    """Handles controlled creation of new LibraryOpacViewsMaster records."""
    model = LibraryOpacViewsMaster
    form_class = LibraryOpacViewsMasterForm
    template_name = "library/library_opac_views_form.html"
    success_url = reverse_lazy("library:library_opac_views_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"LibraryOpacViews '{self.object.code}' created successfully.")
        return response

class LibraryOpacViewsUpdateView(UpdateView):
    """Handles updates and edits to existing LibraryOpacViewsMaster records."""
    model = LibraryOpacViewsMaster
    form_class = LibraryOpacViewsMasterForm
    template_name = "library/library_opac_views_form.html"
    success_url = reverse_lazy("library:library_opac_views_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"LibraryOpacViews '{self.object.code}' updated successfully.")
        return response

class LibraryOpacViewsDeleteView(DeleteView):
    """Handles controlled removal of LibraryOpacViewsMaster records."""
    model = LibraryOpacViewsMaster
    template_name = "library/library_opac_views_confirm_delete.html"
    success_url = reverse_lazy("library:library_opac_views_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"LibraryOpacViews '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class LibraryOpacViewsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = LibraryOpacViewsMaster
    template_name = "library/library_opac_views_print.html"
    context_object_name = "record"

class LibraryOpacViewsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "library/library_opac_views_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = LibraryOpacViewsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = LibraryOpacViewsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_library_opac_views_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="library_opac_views_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in LibraryOpacViewsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_library_opac_views_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in LibraryOpacViewsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
