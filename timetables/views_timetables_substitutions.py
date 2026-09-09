"""
Class-Based Views for Timetables: Faculty Substitutions
PR #34: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from timetables.models_timetables_substitutions import TimetablesSubstitutionsMaster, TimetablesSubstitutionsConfiguration, TimetablesSubstitutionsAuditTransaction
from timetables.forms_timetables_substitutions import TimetablesSubstitutionsMasterForm, TimetablesSubstitutionsSearchFilterForm, TimetablesSubstitutionsBatchActionForm
from timetables.services_timetables_substitutions import TimetablesSubstitutionsWorkflowService, TimetablesSubstitutionsAuditReportingService

class TimetablesSubstitutionsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = TimetablesSubstitutionsMaster
    template_name = "timetables/timetables_substitutions_list.html"
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
        ctx["filter_form"] = TimetablesSubstitutionsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = TimetablesSubstitutionsBatchActionForm()
        ctx["kpis"] = TimetablesSubstitutionsWorkflowService.calculate_domain_kpis()
        return ctx

class TimetablesSubstitutionsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = TimetablesSubstitutionsMaster
    template_name = "timetables/timetables_substitutions_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = TimetablesSubstitutionsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = TimetablesSubstitutionsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class TimetablesSubstitutionsCreateView(CreateView):
    """Handles controlled creation of new TimetablesSubstitutionsMaster records."""
    model = TimetablesSubstitutionsMaster
    form_class = TimetablesSubstitutionsMasterForm
    template_name = "timetables/timetables_substitutions_form.html"
    success_url = reverse_lazy("timetables:timetables_substitutions_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TimetablesSubstitutions '{self.object.code}' created successfully.")
        return response

class TimetablesSubstitutionsUpdateView(UpdateView):
    """Handles updates and edits to existing TimetablesSubstitutionsMaster records."""
    model = TimetablesSubstitutionsMaster
    form_class = TimetablesSubstitutionsMasterForm
    template_name = "timetables/timetables_substitutions_form.html"
    success_url = reverse_lazy("timetables:timetables_substitutions_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"TimetablesSubstitutions '{self.object.code}' updated successfully.")
        return response

class TimetablesSubstitutionsDeleteView(DeleteView):
    """Handles controlled removal of TimetablesSubstitutionsMaster records."""
    model = TimetablesSubstitutionsMaster
    template_name = "timetables/timetables_substitutions_confirm_delete.html"
    success_url = reverse_lazy("timetables:timetables_substitutions_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"TimetablesSubstitutions '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class TimetablesSubstitutionsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = TimetablesSubstitutionsMaster
    template_name = "timetables/timetables_substitutions_print.html"
    context_object_name = "record"

class TimetablesSubstitutionsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "timetables/timetables_substitutions_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = TimetablesSubstitutionsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = TimetablesSubstitutionsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_timetables_substitutions_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="timetables_substitutions_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in TimetablesSubstitutionsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_timetables_substitutions_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in TimetablesSubstitutionsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
