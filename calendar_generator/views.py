"""Calendar views"""

from dataclasses import dataclass
from datetime import date

from typing import Dict, Any

from io import BytesIO
from django.http.response import HttpResponseBadRequest

from django.views.generic import DetailView, ListView, View
from django.http import FileResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404

from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from reportlab.lib.units import inch

from . import models
from . import grids
from . import pdf_presets
from . import pdf


@dataclass
class MonthGrid:
    """Data class representing the month with its grid"""

    year: int
    month: int
    grid: grids.CalendarGrid

    @property
    def first_date(self) -> date:
        """The date of the first day of the month in the grid"""

        return date(self.year, self.month, 1)


class Calendars(ListView):
    """List of all the calendars"""

    model = models.Calendar


class Calendar(DetailView):
    """Calendar pages with everything about the calendar"""

    model = models.Calendar
    template_name = "calendar_generator/calendar.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        assert isinstance(self.object, models.Calendar)

        months = set()

        days_dict = self.object.get_date_letter_map()
        days_list = [(date, letter) for date, letter in days_dict.items()]

        for date_key in days_dict:
            months.add((date_key.year, date_key.month))

        month_grids = []
        # Shove all the HTML calendars in
        for year, month in sorted(months):
            gen = grids.CalendarGridGenerator(days_dict, year, month, 6)
            month_grids.append(MonthGrid(year=year, month=month, grid=gen.get_grid()))

        today = date.today()

        context["today_letter"] = None
        context["today"] = today

        if today in days_dict:
            context["today_letter"] = days_dict[today]

        context['days'] = days_list
        context['calendars'] = month_grids

        return context


class PDFMonth(View):
    """PDF views of a single calendar month"""

    def get(self, request, calendar_id: int, year: int, month: int, preset_slug='black'):
        """Get method for the calendar PDF"""

        del request  # Make the linter happy

        try:
            style = pdf_presets.PRESET_MAP[preset_slug]
        except KeyError:
            return HttpResponseNotFound()

        calendar = get_object_or_404(models.Calendar, pk=calendar_id)
        assert isinstance(calendar, models.Calendar)

        letter_map = calendar.get_date_letter_map()

        if not letter_map:
            return HttpResponseBadRequest()

        grid_generator = grids.CalendarGridGenerator(letter_map, year, month, 6)
        grid = grid_generator.get_grid()

        buf = BytesIO()

        draw_on = canvas.Canvas(buf, pagesize=pagesizes.landscape(pagesizes.letter))
        gen = pdf.CalendarGenerator(canvas=draw_on, grid=grid, style=style, left_offset=.5*inch,
                                    bottom_offset=.5*inch, width=10*inch, height=7.5*inch)
        gen.draw()
        draw_on.showPage()
        draw_on.save()

        buf.seek(0)
        return FileResponse(buf, filename=f"{year}-{month}.pdf")
