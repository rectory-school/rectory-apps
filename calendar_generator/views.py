"""Calendar views"""

import dataclasses
from dataclasses import dataclass
from datetime import date

from typing import Dict, Any, Optional, Tuple

from io import BytesIO

import math

from django.http.response import HttpResponse
from django.views.generic import DetailView, ListView, View
from django.http import FileResponse, HttpResponseNotFound
from django.contrib.auth.mixins import PermissionRequiredMixin

from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from reportlab.lib.units import inch

from . import models
from . import grids
from . import pdf_presets
from . import pdf

ONE_PAGE_PDF_COL_COUNT = 2


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


class CalendarViewPermissionRequired(PermissionRequiredMixin):
    """Require view permission for calendars"""

    permission_required = 'calendar_generator.view_calendar'


class Calendars(CalendarViewPermissionRequired, ListView):
    """List of all the calendars"""

    model = models.Calendar


class Calendar(CalendarViewPermissionRequired, DetailView):
    """Calendar pages with everything about the calendar"""

    model = models.Calendar
    template_name = "calendar_generator/calendar.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        assert isinstance(self.object, models.Calendar)

        months = set()

        days_dict = self.object.get_date_letter_map()

        for date_key in days_dict:
            months.add((date_key.year, date_key.month))

        month_grids = []
        # Shove all the HTML calendars in
        for year, month in sorted(months):
            gen = grids.CalendarGridGenerator(date_letter_map=days_dict, year=year, month=month)
            month_grids.append(MonthGrid(year=year, month=month, grid=gen.get_grid()))

        today = date.today()

        context["today_letter"] = None
        context["today"] = today

        context["style_presets"] = [(i, name) for i, (name, _) in enumerate(pdf_presets.AVAILABLE_COLOR_PRESETS)]

        if today in days_dict:
            context["today_letter"] = days_dict[today]

        context['day_rotation'] = [d.letter for d in self.object.days.all()]
        context['skipped_days'] = sorted((s.date, s.end_date) for s in self.object.skips.all())

        context['calendars'] = month_grids

        return context


class PDFBaseView(CalendarViewPermissionRequired, View):
    """Base view that will have both a calendar and a style"""

    default_page_size = pagesizes.landscape(pagesizes.letter)
    default_left_margin = .5*inch
    default_right_margin = .5*inch
    default_top_margin = .5*inch
    default_bottom_margin = .5*inch

    default_creator = "Rectory Apps System"
    default_subject = None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self._calendar = None
        self._style = None
        self._letter_map = None
        self._canvas = None

    @property
    def is_embedded(self) -> bool:
        """Determine if we've got the embedded flag"""

        return "embedded" in self.request.GET

    @property
    def page_size(self) -> Tuple[float, float]:
        """Return the page size in points for Reportlab"""

        return self.default_page_size

    @property
    def left_margin(self):
        """Proxy left margin"""

        if self.is_embedded:
            return 0

        return self.default_left_margin

    @property
    def right_margin(self):
        """Proxy right margin"""

        if self.is_embedded:
            return 0

        return self.default_right_margin

    @property
    def bottom_margin(self):
        """Proxy bottom margin"""

        if self.is_embedded:
            return 0

        return self.default_bottom_margin

    @property
    def top_margin(self):
        """Proxy top margin"""

        if self.is_embedded:
            return 0

        return self.default_top_margin

    @property
    def inner_height(self):
        """Inner height of the page - the drawable area"""

        return self.page_size[1] - self.top_margin - self.bottom_margin

    @property
    def inner_width(self):
        """Inner width of the page - the drawable area"""

        return self.page_size[0] - self.left_margin - self.right_margin

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """Get proxy to the handler"""

        # These can be accessed via self
        del args
        del kwargs
        del request

        calendar_id = self.kwargs["calendar_id"]

        try:
            calendar = models.Calendar.objects.get(pk=calendar_id)
            assert isinstance(calendar, models.Calendar)
            self._calendar = calendar
            self._letter_map = calendar.get_date_letter_map()

        except models.Calendar.DoesNotExist:
            return HttpResponseNotFound()

        try:
            style = pdf_presets.AVAILABLE_COLOR_PRESETS[self.kwargs['style_index']][1]
        except IndexError:
            return HttpResponseNotFound("That color preset could not be found")

        if self.is_embedded:
            style = dataclasses.copy.copy(style)
            assert isinstance(style, pdf.CalendarStyle)
            style.outline_color = None

        self._style = style

        buf = BytesIO()
        self._canvas = canvas.Canvas(buf, pagesize=self.page_size)

        self.draw_pdf()

        if author := self.get_author():
            self._canvas.setAuthor(author)

        if title := self.get_title():
            self._canvas.setTitle(title)

        if creator := self.get_creator():
            self._canvas.setCreator(creator)

        if subject := self.get_subject():
            self._canvas.setSubject(subject)

        self._canvas.save()
        buf.seek(0)

        return FileResponse(buf, filename=self.get_filename())

    def get_title(self) -> Optional[str]:
        """Get the title to use for the PDF"""

        return self._calendar.title

    def get_author(self) -> Optional[str]:
        """Get the author to use for the PDF"""

        if self.request.user.is_authenticated:
            return str(self.request.user)

    def get_creator(self) -> Optional[str]:
        """Get the creator to use for the PDF"""

        return self.default_creator

    def get_subject(self) -> Optional[str]:
        """Get the subject to use for the PDf"""

        return self.default_subject

    def draw_pdf(self):
        """Draw the actual PDF"""

        raise NotImplementedError

    def get_filename(self) -> str:
        """Return the filename for the PDF"""

        raise NotImplementedError


class PDFMonth(PDFBaseView):
    """PDF views of a single calendar month"""

    def draw_pdf(self):
        year = self.kwargs["year"]
        month = self.kwargs["month"]

        grid_generator = grids.CalendarGridGenerator(date_letter_map=self._letter_map, year=year, month=month)
        grid = grid_generator.get_grid()

        gen = pdf.CalendarGenerator(canvas=self._canvas, grid=grid, style=self._style,
                                    left_offset=self.left_margin, bottom_offset=self.bottom_margin,
                                    width=self.inner_width, height=self.inner_height)

        gen.draw()
        self._canvas.showPage()

    def get_filename(self) -> str:
        year = self.kwargs["year"]
        month = self.kwargs["month"]

        return f"{self._calendar.title} - {year}-{month:02d}.pdf"

    def get_title(self) -> Optional[str]:
        sample_date = date(self.kwargs["year"], self.kwargs["month"], 1)

        return f"{self._calendar.title}: {sample_date.strftime('%B %Y')}"


class PDFMonths(PDFBaseView):
    """All the month calendars in one PDF"""

    def draw_pdf(self):
        all_months = set()

        for day in self._letter_map:
            all_months.add((day.year, day.month))

        for year, month in sorted(all_months):
            grid_generator = grids.CalendarGridGenerator(date_letter_map=self._letter_map, year=year, month=month)
            grid = grid_generator.get_grid()

            gen = pdf.CalendarGenerator(canvas=self._canvas, grid=grid, style=self._style,
                                        left_offset=self.left_margin, bottom_offset=self.bottom_margin,
                                        width=self.inner_width, height=self.inner_height)
            gen.draw()
            self._canvas.showPage()

    def get_filename(self) -> str:
        return f"{self._calendar.title} - All Months.pdf"

    def get_title(self) -> Optional[str]:
        return f"{self._calendar.title}: Full Calendar"


class PDFOnePage(PDFBaseView):
    """All the month calendars in one PDF"""

    page_size = pagesizes.letter

    def draw_pdf(self):
        all_months = set()

        for day in self._letter_map:
            all_months.add((day.year, day.month))

        cal_count = len(all_months)
        col_width = ((8.5 - .5 - .5) * inch) / ONE_PAGE_PDF_COL_COUNT

        # I think newer versions of Python will return a float from int / int,
        # but I don't feel like testing it and want a guarantee for rounding up
        row_count = math.ceil(cal_count / float(ONE_PAGE_PDF_COL_COUNT))

        row_height = ((11 - .5 - .5) * inch / row_count)
        all_months = sorted(all_months)

        row_pad = row_height * .1
        col_pad = col_width * .1

        style = dataclasses.copy.copy(self._style)
        assert isinstance(style, pdf.CalendarStyle)

        # Find the longest header to calculate the size
        all_headers = [date(year, month, 1).strftime("%B %Y") for year, month in all_months]
        longest_header = sorted(all_headers, key=len, reverse=True)[0]

        # Fix the header size so the calendars line up across the page
        style.title_font_size = pdf.get_font_size_maximum_width(
            longest_header, col_width/2, style.title_font_name)

        for row_index in range(row_count):
            for col_index in range(ONE_PAGE_PDF_COL_COUNT):
                cal_index = row_index * ONE_PAGE_PDF_COL_COUNT + col_index

                try:
                    year, month = all_months[cal_index]
                except IndexError:
                    # This might happen on the last calendar
                    continue

                grid_generator = grids.CalendarGridGenerator(date_letter_map=self._letter_map, year=year, month=month)
                grid = grid_generator.get_grid()

                left_offset = self.left_margin + col_index * (col_width + col_pad)

                # We index the months from top to bottom, but we draw the page from bottom to top.
                # Flip the row draw positions
                bottom_offset = self.page_size[0] + self.top_margin - (self.bottom_margin + row_index * (row_height))

                gen = pdf.CalendarGenerator(canvas=self._canvas, grid=grid, style=style,
                                            left_offset=left_offset, bottom_offset=bottom_offset,
                                            width=(col_width - col_pad), height=(row_height - row_pad))

                gen.draw()

    def get_title(self) -> Optional[str]:
        return f"{self._calendar.title}: One Page View"

    def get_filename(self) -> str:
        return f"{self._calendar.title} - One Page.pdf"
