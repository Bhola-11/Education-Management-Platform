"""
Class-Based Views for Library: Reservations & Holds
PR #69: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from library.models_library_reservations import LibraryReservationsMaster, LibraryReservationsConfiguration, LibraryReservationsAuditTransaction
from library.forms_library_reservations import LibraryReservationsMasterForm, LibraryReservationsSearchFilterForm, LibraryReservationsBatchActionForm
from library.services_library_reservations import LibraryReservationsWorkflowService, LibraryReservationsAuditReportingService

class LibraryReservationsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = LibraryReservationsMaster
    template_name = "library/library_reservations_list.html"
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
        ctx["filter_form"] = LibraryReservationsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = LibraryReservationsBatchActionForm()
        ctx["kpis"] = LibraryReservationsWorkflowService.calculate_domain_kpis()
        return ctx

class LibraryReservationsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = LibraryReservationsMaster
    template_name = "library/library_reservations_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = LibraryReservationsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = LibraryReservationsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class LibraryReservationsCreateView(CreateView):
    """Handles controlled creation of new LibraryReservationsMaster records."""
    model = LibraryReservationsMaster
    form_class = LibraryReservationsMasterForm
    template_name = "library/library_reservations_form.html"
    success_url = reverse_lazy("library:library_reservations_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"LibraryReservations '{self.object.code}' created successfully.")
        return response

class LibraryReservationsUpdateView(UpdateView):
    """Handles updates and edits to existing LibraryReservationsMaster records."""
    model = LibraryReservationsMaster
    form_class = LibraryReservationsMasterForm
    template_name = "library/library_reservations_form.html"
    success_url = reverse_lazy("library:library_reservations_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"LibraryReservations '{self.object.code}' updated successfully.")
        return response

class LibraryReservationsDeleteView(DeleteView):
    """Handles controlled removal of LibraryReservationsMaster records."""
    model = LibraryReservationsMaster
    template_name = "library/library_reservations_confirm_delete.html"
    success_url = reverse_lazy("library:library_reservations_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"LibraryReservations '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class LibraryReservationsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = LibraryReservationsMaster
    template_name = "library/library_reservations_print.html"
    context_object_name = "record"

class LibraryReservationsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "library/library_reservations_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = LibraryReservationsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = LibraryReservationsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_library_reservations_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="library_reservations_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in LibraryReservationsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_library_reservations_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in LibraryReservationsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
