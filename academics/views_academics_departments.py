"""
Class-Based Views for Academics: Departments & Faculties
PR #8: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from academics.models_academics_departments import AcademicsDepartmentsMaster, AcademicsDepartmentsConfiguration, AcademicsDepartmentsAuditTransaction
from academics.forms_academics_departments import AcademicsDepartmentsMasterForm, AcademicsDepartmentsSearchFilterForm, AcademicsDepartmentsBatchActionForm
from academics.services_academics_departments import AcademicsDepartmentsWorkflowService, AcademicsDepartmentsAuditReportingService

class AcademicsDepartmentsListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = AcademicsDepartmentsMaster
    template_name = "academics/academics_departments_list.html"
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
        ctx["filter_form"] = AcademicsDepartmentsSearchFilterForm(self.request.GET)
        ctx["batch_form"] = AcademicsDepartmentsBatchActionForm()
        ctx["kpis"] = AcademicsDepartmentsWorkflowService.calculate_domain_kpis()
        return ctx

class AcademicsDepartmentsDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = AcademicsDepartmentsMaster
    template_name = "academics/academics_departments_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = AcademicsDepartmentsAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = AcademicsDepartmentsAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class AcademicsDepartmentsCreateView(CreateView):
    """Handles controlled creation of new AcademicsDepartmentsMaster records."""
    model = AcademicsDepartmentsMaster
    form_class = AcademicsDepartmentsMasterForm
    template_name = "academics/academics_departments_form.html"
    success_url = reverse_lazy("academics:academics_departments_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AcademicsDepartments '{self.object.code}' created successfully.")
        return response

class AcademicsDepartmentsUpdateView(UpdateView):
    """Handles updates and edits to existing AcademicsDepartmentsMaster records."""
    model = AcademicsDepartmentsMaster
    form_class = AcademicsDepartmentsMasterForm
    template_name = "academics/academics_departments_form.html"
    success_url = reverse_lazy("academics:academics_departments_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"AcademicsDepartments '{self.object.code}' updated successfully.")
        return response

class AcademicsDepartmentsDeleteView(DeleteView):
    """Handles controlled removal of AcademicsDepartmentsMaster records."""
    model = AcademicsDepartmentsMaster
    template_name = "academics/academics_departments_confirm_delete.html"
    success_url = reverse_lazy("academics:academics_departments_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"AcademicsDepartments '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class AcademicsDepartmentsPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = AcademicsDepartmentsMaster
    template_name = "academics/academics_departments_print.html"
    context_object_name = "record"

class AcademicsDepartmentsAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "academics/academics_departments_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = AcademicsDepartmentsWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = AcademicsDepartmentsMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_academics_departments_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="academics_departments_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in AcademicsDepartmentsMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_academics_departments_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in AcademicsDepartmentsMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
