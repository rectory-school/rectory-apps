"""Calendar views"""

import dataclasses
from dataclasses import dataclass
from datetime import date
import calendar
import functools

from typing import Dict, Any, Optional, Tuple

from io import BytesIO

import math

from django.views.generic import DetailView, ListView, View, FormView

from django.http import FileResponse, HttpResponseNotFound, HttpResponse, HttpRequest
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404

from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from reportlab.lib.units import inch, mm

from . import models
from . import grids
from . import pdf_presets
from . import pdf
from . import forms

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
        labels_dict = self.object.get_arbitrary_labels()

        for date_key in days_dict:
            months.add((date_key.year, date_key.month))

        month_grids = []
        # Shove all the HTML calendars in
        for year, month in sorted(months):
            start_date = date(year, month, 1)
            _, end_day = calendar.monthrange(year, month)
            end_date = date(year, month, end_day)

            gen = grids.CalendarGridGenerator(date_letter_map=days_dict,
                                              label_map=labels_dict,
                                              start_date=start_date,
                                              end_date=end_date)
            month_grids.append(MonthGrid(year=year, month=month, grid=gen.get_grid()))

        today = date.today()

        context["today_letter"] = None
        context["today"] = today

        context["styles"] = [(i, name) for i, (name, _) in enumerate(pdf_presets.AVAILABLE_STYLE_PRESETS)]
        context["layouts"] = [(i, name) for i, (name, _) in enumerate(pdf_presets.AVAILABLE_LAYOUT_PRESETS)]

        if today in days_dict:
            context["today_letter"] = days_dict[today]

        context['day_rotation'] = [d.letter for d in self.object.days.all()]
        context['skipped_days'] = sorted((s.date, s.end_date) for s in self.object.skips.all())
        context['reset_days'] = [(obj.date, obj.day.letter)
                                 for obj in self.object.reset_days.select_related('day').all()]

        context['calendars'] = month_grids
        context['custom_calendar_form'] = forms.CustomCalendarForm(calendar=self.object)

        return context


class CustomPDF(FormView):
    """FormView for custom PDF"""

    template_name = "calendar_generator/custom_pdf.html"
    form_class = forms.CustomCalendarForm

    def form_valid(self, form: forms.CustomCalendarForm) -> HttpResponse:
        calendar_obj = self.get_calendar()

        size_index = int(form.cleaned_data["size"])
        title = form.cleaned_data["title"]
        style_index = int(form.cleaned_data["style"])
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]

        letter_map = calendar_obj.get_date_letter_map()
        label_map = calendar_obj.get_arbitrary_labels()

        grid_generator = grids.CalendarGridGenerator(date_letter_map=letter_map,
                                                     label_map=label_map,
                                                     start_date=start_date,
                                                     end_date=end_date,
                                                     custom_title=title)
        grid = grid_generator.get_grid()

        _, style = pdf_presets.AVAILABLE_STYLE_PRESETS[style_index]
        _, size = pdf_presets.AVAILABLE_LAYOUT_PRESETS[size_index]

        buf = BytesIO()
        pdf_canvas = canvas.Canvas(buf, pagesize=(size.width, size.height))

        gen = pdf.CalendarGenerator(canvas=pdf_canvas, grid=grid, style=style,
                                    left_offset=size.left_margin, bottom_offset=size.bottom_margin,
                                    width=size.inner_width, height=size.inner_height)

        gen.draw()
        pdf_canvas.showPage()
        pdf_canvas.save()
        buf.seek(0)

        file_name = f"{calendar_obj.title} - {start_date} to {end_date}.pdf"

        return FileResponse(buf, filename=file_name)

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()

        kwargs["calendar"] = self.get_calendar()

        return kwargs

    def get_context_data(self, **kwargs: Dict[str, any]) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["calendar"] = self.get_calendar()

        return context

    @functools.cache
    def get_calendar(self) -> models.Calendar:
        """Get the calendar we are working on"""

        return get_object_or_404(models.Calendar, pk=self.kwargs["calendar_id"])


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
        self._label_map = None

        self._canvas = None

    def get_style_index(self) -> int:
        """Get the style index to use"""

        return self.kwargs['style_index']

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
            calendar_obj = models.Calendar.objects.get(pk=calendar_id)
            assert isinstance(calendar_obj, models.Calendar)
            self._calendar = calendar_obj
            self._letter_map = calendar_obj.get_date_letter_map()
            self._label_map = calendar_obj.get_arbitrary_labels()

        except models.Calendar.DoesNotExist:
            return HttpResponseNotFound()

        try:
            style = pdf_presets.AVAILABLE_STYLE_PRESETS[self.get_style_index()][1]
        except IndexError:
            return HttpResponseNotFound("That color preset could not be found")

        if self.is_embedded:
            style = dataclasses.copy.copy(style)
            assert isinstance(style, pdf.FormatStyle)
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


class PDFMonth(View):
    """PDF views of a single calendar month"""

    def get(self, request: HttpRequest, calendar_id: int, year: int, month: int,
            style_index: int, layout_index: int) -> HttpResponse:
        """Get method returning an individual month PDF"""

        try:
            calendar_obj = models.Calendar.objects.get(pk=calendar_id)
            assert isinstance(calendar_obj, models.Calendar)

            start_date = date(year, month, 1)
            _, end_day = calendar.monthrange(year, month)
            end_date = date(year, month, end_day)

            _, style = pdf_presets.AVAILABLE_STYLE_PRESETS[style_index]
            _, layout = pdf_presets.AVAILABLE_LAYOUT_PRESETS[layout_index]
        except (ValueError, models.Calendar.DoesNotExist, IndexError):
            return HttpResponseNotFound()

        date_letter_map = calendar_obj.get_date_letter_map()
        label_map = calendar_obj.get_arbitrary_labels()

        buf = BytesIO()
        pdf_canvas = canvas.Canvas(buf, pagesize=(layout.width, layout.height))

        if request.user.is_authenticated:
            pdf_canvas.setAuthor(str(request.user))

        pdf_canvas.setTitle(calendar_obj.title)
        pdf_canvas.setCreator("Rectory Apps System")
        pdf_canvas.setSubject("Calendar")

        grid_generator = grids.CalendarGridGenerator(date_letter_map, label_map, start_date, end_date)
        grid = grid_generator.get_grid()

        generator = pdf.CalendarGenerator(pdf_canvas, grid, style, layout)
        generator.draw()

        pdf_canvas.save()

        buf.seek(0)
        return FileResponse(buf, filename=f"{year}-{month:02d}.pdf")


class PDFMonths(View):
    """All the month calendars in one PDF"""

    def get(self, request: HttpRequest, calendar_id: int,
            style_index: int, layout_index: int) -> HttpResponse:
        """Get method returning an individual month PDF"""

        try:
            calendar_obj = models.Calendar.objects.get(pk=calendar_id)
            assert isinstance(calendar_obj, models.Calendar)

            _, style = pdf_presets.AVAILABLE_STYLE_PRESETS[style_index]
            _, layout = pdf_presets.AVAILABLE_LAYOUT_PRESETS[layout_index]
        except (models.Calendar.DoesNotExist, IndexError):
            return HttpResponseNotFound()

        date_letter_map = calendar_obj.get_date_letter_map()
        label_map = calendar_obj.get_arbitrary_labels()

        buf = BytesIO()
        pdf_canvas = canvas.Canvas(buf, pagesize=(layout.width, layout.height))

        if request.user.is_authenticated:
            pdf_canvas.setAuthor(str(request.user))

        pdf_canvas.setTitle(calendar_obj.title)
        pdf_canvas.setCreator("Rectory Apps System")
        pdf_canvas.setSubject("Calendar")

        all_months = set()
        for used_date in date_letter_map | label_map:
            all_months.add((used_date.year, used_date.month))

        for year, month in sorted(all_months):
            start_date = date(year, month, 1)
            _, end_day = calendar.monthrange(year, month)
            end_date = date(year, month, end_day)

            grid_generator = grids.CalendarGridGenerator(date_letter_map, label_map, start_date, end_date)
            grid = grid_generator.get_grid()

            generator = pdf.CalendarGenerator(pdf_canvas, grid, style, layout)
            generator.draw()

            pdf_canvas.showPage()

        pdf_canvas.save()

        buf.seek(0)
        return FileResponse(buf, filename=f"{calendar_obj.title} - All Months.pdf")


class PDFOnePage(View):
    """All the month calendars in one PDF"""

    def get(self, request: HttpRequest, calendar_id: int,
            style_index: int, layout_index: int) -> HttpResponse:
        """Get method returning an individual month PDF"""

        try:
            calendar_obj = models.Calendar.objects.get(pk=calendar_id)
            assert isinstance(calendar_obj, models.Calendar)

            _, style = pdf_presets.AVAILABLE_STYLE_PRESETS[style_index]
            _, layout = pdf_presets.AVAILABLE_LAYOUT_PRESETS[layout_index]
        except (models.Calendar.DoesNotExist, IndexError):
            return HttpResponseNotFound()

        date_letter_map = calendar_obj.get_date_letter_map()
        label_map = calendar_obj.get_arbitrary_labels()

        buf = BytesIO()
        pdf_canvas = canvas.Canvas(buf, pagesize=(layout.width, layout.height))

        if request.user.is_authenticated:
            pdf_canvas.setAuthor(str(request.user))

        pdf_canvas.setTitle(calendar_obj.title)
        pdf_canvas.setCreator("Rectory Apps System")
        pdf_canvas.setSubject("Calendar")

        all_months = set()
        for used_date in date_letter_map | label_map:
            all_months.add((used_date.year, used_date.month))

        row_count = math.ceil(len(all_months)/ONE_PAGE_PDF_COL_COUNT)
        layouts = layout.subdivide(row_count, ONE_PAGE_PDF_COL_COUNT, 5*mm, 10*mm)

        for i, (year, month) in enumerate(sorted(all_months)):
            layout = layouts[i]

            start_date = date(year, month, 1)
            _, end_day = calendar.monthrange(year, month)
            end_date = date(year, month, end_day)

            grid_generator = grids.CalendarGridGenerator(date_letter_map, label_map, start_date, end_date)
            grid = grid_generator.get_grid()

            generator = pdf.CalendarGenerator(pdf_canvas, grid, style, layout)
            generator.draw()

        pdf_canvas.save()

        buf.seek(0)
        return FileResponse(buf, filename=f"{calendar_obj.title} - All Months.pdf")
