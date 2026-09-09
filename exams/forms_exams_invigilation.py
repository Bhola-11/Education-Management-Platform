"""
Enterprise Forms for Exams: Invigilation Roster
PR #50: Validation Hooks, Clean Methods, Accessible Layouts.
"""

from django import forms
from django.core.exceptions import ValidationError
from exams.models_exams_invigilation import ExamsInvigilationMaster, ExamsInvigilationConfiguration, ExamsInvigilationLedger

class ExamsInvigilationMasterForm(forms.ModelForm):
    """Primary form for creating and updating ExamsInvigilationMaster records."""
    class Meta:
        model = ExamsInvigilationMaster
        fields = [
            "code", "name", "description", "priority", "status",
            "capacity_limit", "allocated_count", "monetary_value",
            "score_rating", "effective_date", "expiration_date", "is_active"
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. EXAMS_INVIGILATION-001"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Descriptive institutional name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "priority": forms.NumberInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "capacity_limit": forms.NumberInput(attrs={"class": "form-control"}),
            "allocated_count": forms.NumberInput(attrs={"class": "form-control"}),
            "monetary_value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "score_rating": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "effective_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "expiration_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_code(self):
        code = self.cleaned_data.get("code", "").strip().upper()
        if len(code) < 3:
            raise ValidationError("Entity code must be at least 3 characters.")
        return code

    def clean(self):
        cleaned_data = super().clean()
        eff = cleaned_data.get("effective_date")
        exp = cleaned_data.get("expiration_date")
        cap = cleaned_data.get("capacity_limit", 0)
        alloc = cleaned_data.get("allocated_count", 0)
        
        if eff and exp and eff > exp:
            raise ValidationError("Effective date cannot be subsequent to expiration date.")
        if alloc > cap:
            raise ValidationError("Allocated count cannot exceed capacity limit.")
        return cleaned_data

class ExamsInvigilationConfigurationForm(forms.ModelForm):
    """Configuration form for setting policy limits and weights."""
    class Meta:
        model = ExamsInvigilationConfiguration
        fields = ["code", "name", "description", "priority", "status", "capacity_limit", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "priority": forms.NumberInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "capacity_limit": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class ExamsInvigilationLedgerEntryForm(forms.ModelForm):
    """Form for posting quantitative or financial transactions."""
    class Meta:
        model = ExamsInvigilationLedger
        fields = ["code", "name", "monetary_value", "status", "description"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "monetary_value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

class ExamsInvigilationBatchActionForm(forms.Form):
    """Form for processing bulk updates across selected records."""
    action = forms.ChoiceField(
        choices=[
            ("ACTIVATE", "Mark Active"),
            ("DEACTIVATE", "Mark Inactive"),
            ("LOCK", "Administrative Lock"),
            ("UNLOCK", "Release Lock"),
            ("ARCHIVE", "Archive Selected")
        ],
        widget=forms.Select(attrs={"class": "form-select"})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Reason for bulk action..."})
    )

class ExamsInvigilationSearchFilterForm(forms.Form):
    """Comprehensive search and filtration toolbar form."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Search by code or title..."})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All Statuses"), ("ACTIVE", "Active"), ("SUSPENDED", "Suspended"), ("ARCHIVED", "Archived")],
        widget=forms.Select(attrs={"class": "form-select"})
    )
    is_active = forms.ChoiceField(
        required=False,
        choices=[("", "All"), ("1", "Active Only"), ("0", "Inactive Only")],
        widget=forms.Select(attrs={"class": "form-select"})
    )
    min_score = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Min Score..."})
    )
