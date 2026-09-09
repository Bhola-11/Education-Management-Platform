"""Accessible Form Widgets and Rendering Helpers."""
from django import forms

class DatePickerWidget(forms.DateInput):
    input_type = 'date'
    def __init__(self, attrs=None):
        default_attrs = {'class': 'form-control', 'autocomplete': 'off'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

class TimePickerWidget(forms.TimeInput):
    input_type = 'time'
    def __init__(self, attrs=None):
        default_attrs = {'class': 'form-control'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
