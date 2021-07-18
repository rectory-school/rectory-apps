"""Calendar views"""

from dataclasses import dataclass
from datetime import date

from typing import Dict, Any

from io import BytesIO
from django.http.response import HttpResponse, HttpResponseBadRequest

from django.views.generic import DetailView, ListView, View
from django.http import FileResponse, HttpResponseNotFound

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


class CalendarStylePDFBaseView(View):
    """Base view that will have both a calendar and a style"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self._calendar = None
        self._style = None
        self._letter_map = None

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """Get proxy to the handler"""

        # These can be accessed via self
        del args
        del kwargs
        del request

        calendar_id = self.kwargs["calendar_id"]
        style_slug = self.kwargs.get("preset_slug", "black")

        try:
            calendar = models.Calendar.objects.get(pk=calendar_id)
            assert isinstance(calendar, models.Calendar)
            self._calendar = calendar
            self._letter_map = calendar.get_date_letter_map()

            if not self._letter_map:
                return HttpResponseBadRequest()

        except models.Calendar.DoesNotExist:
            return HttpResponseNotFound()

        style = pdf_presets.PRESET_MAP.get(style_slug)

        if not style:
            return HttpResponseNotFound()

        self._style = style

        buf = BytesIO()
        draw_on = canvas.Canvas(buf, pagesize=pagesizes.landscape(pagesizes.letter))

        self.draw_pdf(draw_on)
        draw_on.save()
        buf.seek(0)

        return FileResponse(buf, filename=self.get_filename())

    def draw_pdf(self, draw_on: canvas.Canvas):
        """Draw the actual PDF"""

        raise NotImplementedError

    def get_filename(self) -> str:
        """Return the filename for the PDF"""

        raise NotImplementedError


class PDFMonth(CalendarStylePDFBaseView):
    """PDF views of a single calendar month"""

    def draw_pdf(self, draw_on: canvas.Canvas):
        year = self.kwargs["year"]
        month = self.kwargs["month"]

        grid_generator = grids.CalendarGridGenerator(self._letter_map, year, month, 6)
        grid = grid_generator.get_grid()

        gen = pdf.CalendarGenerator(canvas=draw_on, grid=grid, style=self._style, left_offset=.5*inch,
                                    bottom_offset=.5*inch, width=10*inch, height=7.5*inch)

        gen.draw()
        draw_on.showPage()

    def get_filename(self) -> str:
        year = self.kwargs["year"]
        month = self.kwargs["month"]

        return f"{self._calendar.title} - {year}-{month}.pdf"
