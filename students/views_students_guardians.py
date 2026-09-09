"""
Class-Based Views for Students: Guardians & Parents
PR #17: Full CRUD Lifecycle, Filtering, Statistics, Exporting.
"""

import csv
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import models
from students.models_students_guardians import StudentsGuardiansMaster, StudentsGuardiansConfiguration, StudentsGuardiansAuditTransaction
from students.forms_students_guardians import StudentsGuardiansMasterForm, StudentsGuardiansSearchFilterForm, StudentsGuardiansBatchActionForm
from students.services_students_guardians import StudentsGuardiansWorkflowService, StudentsGuardiansAuditReportingService

class StudentsGuardiansListView(ListView):
    """Data table view with multi-faceted filtering, sorting, and pagination."""
    model = StudentsGuardiansMaster
    template_name = "students/students_guardians_list.html"
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
        ctx["filter_form"] = StudentsGuardiansSearchFilterForm(self.request.GET)
        ctx["batch_form"] = StudentsGuardiansBatchActionForm()
        ctx["kpis"] = StudentsGuardiansWorkflowService.calculate_domain_kpis()
        return ctx

class StudentsGuardiansDetailView(DetailView):
    """In-depth profile displaying master record, details, and audit transactions."""
    model = StudentsGuardiansMaster
    template_name = "students/students_guardians_detail.html"
    context_object_name = "record"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transactions"] = StudentsGuardiansAuditTransaction.objects.filter(name__icontains=self.object.code)[:10]
        ctx["dossier"] = StudentsGuardiansAuditReportingService.compile_audit_dossier(self.object.pk)
        return ctx

class StudentsGuardiansCreateView(CreateView):
    """Handles controlled creation of new StudentsGuardiansMaster records."""
    model = StudentsGuardiansMaster
    form_class = StudentsGuardiansMasterForm
    template_name = "students/students_guardians_form.html"
    success_url = reverse_lazy("students:students_guardians_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"StudentsGuardians '{self.object.code}' created successfully.")
        return response

class StudentsGuardiansUpdateView(UpdateView):
    """Handles updates and edits to existing StudentsGuardiansMaster records."""
    model = StudentsGuardiansMaster
    form_class = StudentsGuardiansMasterForm
    template_name = "students/students_guardians_form.html"
    success_url = reverse_lazy("students:students_guardians_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"StudentsGuardians '{self.object.code}' updated successfully.")
        return response

class StudentsGuardiansDeleteView(DeleteView):
    """Handles controlled removal of StudentsGuardiansMaster records."""
    model = StudentsGuardiansMaster
    template_name = "students/students_guardians_confirm_delete.html"
    success_url = reverse_lazy("students:students_guardians_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.warning(request, f"StudentsGuardians '{obj.code}' was permanently deleted.")
        return super().delete(request, *args, **kwargs)

class StudentsGuardiansPrintView(DetailView):
    """Print-ready layout for institutional documentation and archival."""
    model = StudentsGuardiansMaster
    template_name = "students/students_guardians_print.html"
    context_object_name = "record"

class StudentsGuardiansAnalyticsView(TemplateView):
    """Domain analytics dashboard displaying metrics, histograms, and KPIs."""
    template_name = "students/students_guardians_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["kpis"] = StudentsGuardiansWorkflowService.calculate_domain_kpis()
        ctx["top_records"] = StudentsGuardiansMaster.objects.filter(is_active=True).order_by("-score_rating")[:5]
        return ctx

def export_students_guardians_csv(request):
    """Exports filtered dataset as streaming RFC-4180 CSV document."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="students_guardians_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Status", "Capacity", "Allocated", "Monetary Value", "Effective Date", "Active"])
    
    for r in StudentsGuardiansMaster.objects.all()[:1000]:
        writer.writerow([r.code, r.name, r.status, r.capacity_limit, r.allocated_count, r.monetary_value, r.effective_date, r.is_active])
    return response

def export_students_guardians_json(request):
    """Exports serialized catalog entries as structured JSON payload."""
    data = [r.to_summary_dict() for r in StudentsGuardiansMaster.objects.all()[:500]]
    return JsonResponse({"catalog": data, "count": len(data)}, safe=False)
