"""
Class-Based Views for Library: Library Cataloging
PR #66: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from library.models_library_catalog import LibraryCatalogMaster, LibraryCatalogConfiguration, LibraryCatalogAuditTransaction
from library.forms_library_catalog import LibraryCatalogMasterForm, LibraryCatalogSearchFilterForm, LibraryCatalogBatchActionForm
from library.services_library_catalog import LibraryCatalogWorkflowService, LibraryCatalogAuditReportingService

class LibraryCatalogListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = LibraryCatalogMaster
    template_name = "library/library_catalog_list.html"
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
        ctx["filter_form"] = LibraryCatalogSearchFilterForm(self.request.GET)
        ctx["batch_form"] = LibraryCatalogBatchActionForm()
        ctx["kpis"] = LibraryCatalogWorkflowService.calculate_domain_kpis()
        return ctx

class LibraryCatalogDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = LibraryCatalogMaster
    template_name = "library/library_catalog_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = LibraryCatalogAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = LibraryCatalogAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class LibraryCatalogCreateView(CreateView):
    """Handles controlled creation of new LibraryCatalogMaster records."""
    model = LibraryCatalogMaster
    form_class = LibraryCatalogMasterForm
    template_name = "library/library_catalog_form.html"
    success_url = reverse_lazy("library:library_catalog_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"LibraryCatalog '{self.object.code}' created successfully.")
        return response

class LibraryCatalogUpdateView(UpdateView):
    """Handles updates and edits to existing LibraryCatalogMaster records."""
    model = LibraryCatalogMaster
    form_class = LibraryCatalogMasterForm
    template_name = "library/library_catalog_form.html"
    success_url = reverse_lazy("library:library_catalog_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"LibraryCatalog '{self.object.code}' updated successfully.")
        return response

class LibraryCatalogDeleteView(DeleteView):
    """Handles controlled removal of LibraryCatalogMaster records."""
    model = LibraryCatalogMaster
    template_name = "library/library_catalog_confirm_delete.html"
    success_url = reverse_lazy("library:library_catalog_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"LibraryCatalog '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class LibraryCatalogPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = LibraryCatalogMaster
    template_name = "library/library_catalog_print.html"
    context_object_name = "record"

class LibraryCatalogAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "library/library_catalog_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = LibraryCatalogWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = LibraryCatalogMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_library_catalog_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="library_catalog_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in LibraryCatalogMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_library_catalog_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in LibraryCatalogMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
