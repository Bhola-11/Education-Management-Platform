"""
Class-Based Views for Academics: Prerequisites & Rules
PR #13: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from academics.models_academics_prerequisites import AcademicsPrerequisitesMaster, AcademicsPrerequisitesConfiguration, AcademicsPrerequisitesAuditTransaction
from academics.forms_academics_prerequisites import AcademicsPrerequisitesMasterForm, AcademicsPrerequisitesSearchFilterForm, AcademicsPrerequisitesBatchActionForm
from academics.services_academics_prerequisites import AcademicsPrerequisitesWorkflowService, AcademicsPrerequisitesAuditReportingService

class AcademicsPrerequisitesListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AcademicsPrerequisitesMaster
    template_name = "academics/academics_prerequisites_list.html"
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
        ctx["filter_form"] = AcademicsPrerequisitesSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AcademicsPrerequisitesBatchActionForm()
        ctx["kpis"] = AcademicsPrerequisitesWorkflowService.calculate_domain_kpis()
        return ctx

class AcademicsPrerequisitesDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AcademicsPrerequisitesMaster
    template_name = "academics/academics_prerequisites_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AcademicsPrerequisitesAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AcademicsPrerequisitesAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AcademicsPrerequisitesCreateView(CreateView):
    """Handles controlled creation of new AcademicsPrerequisitesMaster records."""
    model = AcademicsPrerequisitesMaster
    form_class = AcademicsPrerequisitesMasterForm
    template_name = "academics/academics_prerequisites_form.html"
    success_url = reverse_lazy("academics:academics_prerequisites_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AcademicsPrerequisites '{self.object.code}' created successfully.")
        return response

class AcademicsPrerequisitesUpdateView(UpdateView):
    """Handles updates and edits to existing AcademicsPrerequisitesMaster records."""
    model = AcademicsPrerequisitesMaster
    form_class = AcademicsPrerequisitesMasterForm
    template_name = "academics/academics_prerequisites_form.html"
    success_url = reverse_lazy("academics:academics_prerequisites_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AcademicsPrerequisites '{self.object.code}' updated successfully.")
        return response

class AcademicsPrerequisitesDeleteView(DeleteView):
    """Handles controlled removal of AcademicsPrerequisitesMaster records."""
    model = AcademicsPrerequisitesMaster
    template_name = "academics/academics_prerequisites_confirm_delete.html"
    success_url = reverse_lazy("academics:academics_prerequisites_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AcademicsPrerequisites '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AcademicsPrerequisitesPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AcademicsPrerequisitesMaster
    template_name = "academics/academics_prerequisites_print.html"
    context_object_name = "record"

class AcademicsPrerequisitesAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "academics/academics_prerequisites_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AcademicsPrerequisitesWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AcademicsPrerequisitesMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_academics_prerequisites_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="academics_prerequisites_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AcademicsPrerequisitesMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_academics_prerequisites_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AcademicsPrerequisitesMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
