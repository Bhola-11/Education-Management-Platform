"""
Class-Based Views for Academics: Programs & Degrees
PR #9: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from academics.models_academics_programs import AcademicsProgramsMaster, AcademicsProgramsConfiguration, AcademicsProgramsAuditTransaction
from academics.forms_academics_programs import AcademicsProgramsMasterForm, AcademicsProgramsSearchFilterForm, AcademicsProgramsBatchActionForm
from academics.services_academics_programs import AcademicsProgramsWorkflowService, AcademicsProgramsAuditReportingService

class AcademicsProgramsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AcademicsProgramsMaster
    template_name = "academics/academics_programs_list.html"
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
        ctx["filter_form"] = AcademicsProgramsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AcademicsProgramsBatchActionForm()
        ctx["kpis"] = AcademicsProgramsWorkflowService.calculate_domain_kpis()
        return ctx

class AcademicsProgramsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AcademicsProgramsMaster
    template_name = "academics/academics_programs_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AcademicsProgramsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AcademicsProgramsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AcademicsProgramsCreateView(CreateView):
    """Handles controlled creation of new AcademicsProgramsMaster records."""
    model = AcademicsProgramsMaster
    form_class = AcademicsProgramsMasterForm
    template_name = "academics/academics_programs_form.html"
    success_url = reverse_lazy("academics:academics_programs_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AcademicsPrograms '{self.object.code}' created successfully.")
        return response

class AcademicsProgramsUpdateView(UpdateView):
    """Handles updates and edits to existing AcademicsProgramsMaster records."""
    model = AcademicsProgramsMaster
    form_class = AcademicsProgramsMasterForm
    template_name = "academics/academics_programs_form.html"
    success_url = reverse_lazy("academics:academics_programs_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AcademicsPrograms '{self.object.code}' updated successfully.")
        return response

class AcademicsProgramsDeleteView(DeleteView):
    """Handles controlled removal of AcademicsProgramsMaster records."""
    model = AcademicsProgramsMaster
    template_name = "academics/academics_programs_confirm_delete.html"
    success_url = reverse_lazy("academics:academics_programs_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AcademicsPrograms '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AcademicsProgramsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AcademicsProgramsMaster
    template_name = "academics/academics_programs_print.html"
    context_object_name = "record"

class AcademicsProgramsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "academics/academics_programs_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AcademicsProgramsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AcademicsProgramsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_academics_programs_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="academics_programs_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AcademicsProgramsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_academics_programs_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AcademicsProgramsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
