"""Forms for calendars"""

from typing import Dict, Optional
from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from . import models
from . import pdf_presets

SIZE_CHOICES = [(i, title) for (i, (title, _)) in enumerate(pdf_presets.AVAILABLE_LAYOUT_PRESETS)]
STYLE_CHOICES = [(i, title) for (i, (title, _)) in enumerate(pdf_presets.AVAILABLE_STYLE_PRESETS)]


class CustomCalendarForm(forms.Form):
    """Form to generate a custom calendar"""

    layout = forms.ChoiceField(choices=SIZE_CHOICES)
    style = forms.ChoiceField(choices=STYLE_CHOICES)
    title = forms.CharField(max_length=255)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, calendar: models.Calendar, initial: Optional[Dict] = None, **kwargs):
        self._calendar = calendar

        if not initial:
            initial = {}

        initial['start_date'] = calendar.start_date
        initial['end_date'] = calendar.end_date
        initial['title'] = calendar.title

        super().__init__(*args, initial=initial, **kwargs)

    def clean_start_date(self):
        """Make sure the start date is appropriate"""

        start_date = self.cleaned_data['start_date']
        if start_date > self._calendar.end_date:
            raise ValidationError(_("Start date must be before the calendar's end date"))

        return start_date

    def clean_end_date(self):
        """Make sure the end date is appropriate"""

        end_date = self.cleaned_data['end_date']
        if end_date < self._calendar.start_date:
            raise ValidationError(_("End date must be after the calendar's start date"))

        return end_date

    def clean(self):
        """Cross-validate all fields """

        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date:
            assert isinstance(start_date, date)
            assert isinstance(end_date, date)

            if (end_date - start_date).days < 1:
                raise ValidationError(_("End date must be after start date"))

        return cleaned_data
