"""
Class-Based Views for Library: Library Overdue Fines
PR #70: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from library.models_library_fines import LibraryFinesMaster, LibraryFinesConfiguration, LibraryFinesAuditTransaction
from library.forms_library_fines import LibraryFinesMasterForm, LibraryFinesSearchFilterForm, LibraryFinesBatchActionForm
from library.services_library_fines import LibraryFinesWorkflowService, LibraryFinesAuditReportingService

class LibraryFinesListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = LibraryFinesMaster
    template_name = "library/library_fines_list.html"
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
        ctx["filter_form"] = LibraryFinesSearchFilterForm(self.request.GET)
        ctx["batch_form"] = LibraryFinesBatchActionForm()
        ctx["kpis"] = LibraryFinesWorkflowService.calculate_domain_kpis()
        return ctx

class LibraryFinesDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = LibraryFinesMaster
    template_name = "library/library_fines_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = LibraryFinesAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = LibraryFinesAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class LibraryFinesCreateView(CreateView):
    """Handles controlled creation of new LibraryFinesMaster records."""
    model = LibraryFinesMaster
    form_class = LibraryFinesMasterForm
    template_name = "library/library_fines_form.html"
    success_url = reverse_lazy("library:library_fines_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"LibraryFines '{self.object.code}' created successfully.")
        return response

class LibraryFinesUpdateView(UpdateView):
    """Handles updates and edits to existing LibraryFinesMaster records."""
    model = LibraryFinesMaster
    form_class = LibraryFinesMasterForm
    template_name = "library/library_fines_form.html"
    success_url = reverse_lazy("library:library_fines_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"LibraryFines '{self.object.code}' updated successfully.")
        return response

class LibraryFinesDeleteView(DeleteView):
    """Handles controlled removal of LibraryFinesMaster records."""
    model = LibraryFinesMaster
    template_name = "library/library_fines_confirm_delete.html"
    success_url = reverse_lazy("library:library_fines_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"LibraryFines '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class LibraryFinesPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = LibraryFinesMaster
    template_name = "library/library_fines_print.html"
    context_object_name = "record"

class LibraryFinesAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "library/library_fines_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = LibraryFinesWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = LibraryFinesMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_library_fines_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="library_fines_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in LibraryFinesMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_library_fines_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in LibraryFinesMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
