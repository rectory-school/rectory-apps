"""Calendar views"""

from dataclasses import dataclass
from datetime import date
import calendar

from typing import Dict, Any, List, Union

from io import BytesIO

import math
from django.http.response import HttpResponseBadRequest

from django.views.generic import DetailView, ListView

from django.http import FileResponse, HttpRequest
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required

from django.shortcuts import get_object_or_404, render

from reportlab.pdfgen import canvas

from . import models
from . import grids
from . import pdf
from . import forms

ONE_PAGE_PDF_COL_COUNT = 2

VIEW_CALENDAR_PERMISSION = 'calendar_generator.view_calendar'


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

    @property
    def last_date(self) -> date:
        """The date of the last day of the month in the grid"""

        _, end_day = calendar.monthrange(self.year, self.month)
        return date(self.year, self.month, end_day)


class CalendarViewPermissionRequired(PermissionRequiredMixin):
    """Require view permission for calendars"""

    permission_required = VIEW_CALENDAR_PERMISSION


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

        context["styles"] = models.ColorSet.objects.all()
        context["layouts"] = models.Layout.objects.all()
        context["monthly_favorites"] = models.MonthlyDisplaySet.objects.all().select_related("color_set", "layout")
        context["one_page_favorites"] = models.OnePageDisplaySet.objects.all().select_related("color_set", "layout")
        context["show_all_displays"] = "show_all_displays" in self.request.GET

        if today in days_dict:
            context["today_letter"] = days_dict[today]

        context['day_rotation'] = [d.letter for d in self.object.days.all()]
        context['skipped_days'] = sorted((s.date, s.end_date) for s in self.object.skips.all())
        context['reset_days'] = [(obj.date, obj.day.letter)
                                 for obj in self.object.reset_days.select_related('day').all()]

        context['calendars'] = month_grids
        context['custom_calendar_form'] = forms.CustomCalendarForm(calendar=self.object)

        return context


@permission_required(VIEW_CALENDAR_PERMISSION)
def custom_preview(request, calendar_id: int):
    """Custom calendar generation and preview"""

    cal: models.Calendar = get_object_or_404(models.Calendar, pk=calendar_id)
    title = request.GET.get('title', cal.title)

    try:
        start_date = _parse_date(request.GET.get('start_date', cal.start_date))
        end_date = _parse_date(request.GET.get('end_date', cal.end_date))
    except (IndexError, ValueError) as exc:
        return HttpResponseBadRequest(str(exc))

    data = {
        'title': title,
        'start_date': start_date,
        'end_date': end_date,
    }

    form = forms.CustomCalendarForm(data=data, calendar=cal, initial=data)

    context = {
        'request': request,
        'form': form,
        'calendar': cal,

        "styles": models.ColorSet.objects.all(),
        "layouts": models.Layout.objects.all(),

        'start_date': start_date,
        'end_date': end_date,
        'title': title,
    }

    if form.is_bound and form.is_valid():
        letter_map = cal.get_date_letter_map()
        label_map = cal.get_arbitrary_labels()

        f_title = form.cleaned_data["title"]
        f_start = form.cleaned_data["start_date"]
        f_end = form.cleaned_data["end_date"]

        grid_generator = grids.CalendarGridGenerator(date_letter_map=letter_map,
                                                     label_map=label_map,
                                                     start_date=f_start,
                                                     end_date=f_end,
                                                     custom_title=f_title)
        grid = grid_generator.get_grid()

        context["title"] = title
        context["grid"] = grid

    return render(request, "calendar_generator/custom.html", context)


@permission_required(VIEW_CALENDAR_PERMISSION)
def pdf_single_grid(
        request: HttpRequest, calendar_id: int, layout_id: int, style_id: int, start_year: int, start_month: int,
        start_day: int, end_year: int, end_month: int, end_day: int):
    """A PDF grid from start date to end date with a given style and size"""

    cal = get_object_or_404(models.Calendar, pk=calendar_id)

    try:
        style = models.ColorSet.objects.get(pk=style_id).to_style()
        layout = models.Layout.objects.get(pk=layout_id).to_pdf_layout()

    except (ValueError, IndexError, models.ColorSet.DoesNotExist, models.Layout.DoesNotExist) as exc:
        return HttpResponseBadRequest(str(exc))

    letter_map = cal.get_date_letter_map()
    label_map = cal.get_arbitrary_labels()

    if end_day == 0:
        _, end_day = calendar.monthrange(end_year, end_month)

    start_date = date(start_year, start_month, start_day)
    end_date = date(end_year, end_month, end_day)

    title = request.GET.get("title", date(start_year, start_month, 1).strftime("%B %Y"))

    generator = grids.CalendarGridGenerator(date_letter_map=letter_map,
                                            label_map=label_map,
                                            start_date=start_date,
                                            end_date=end_date,
                                            custom_title=title,)

    grid = generator.get_grid()

    buf = BytesIO()
    pdf_canvas = canvas.Canvas(buf, pagesize=(layout.width, layout.height))

    if request.user.is_authenticated:
        pdf_canvas.setAuthor(str(request.user))

    pdf_canvas.setTitle(title)
    pdf_canvas.setCreator("Rectory Apps System")
    pdf_canvas.setSubject("Calendar")

    gen = pdf.CalendarGenerator(pdf_canvas, grid, style, layout)

    gen.draw()
    pdf_canvas.showPage()
    pdf_canvas.save()
    buf.seek(0)

    file_name = f"{cal.title} - {start_date} to {end_date}.pdf"
    return FileResponse(buf, filename=file_name)


@permission_required(VIEW_CALENDAR_PERMISSION)
def pdf_all_months(request, calendar_id: int, style_id: int, layout_id: int):
    """Get a PDF with all a month per page"""

    cal = get_object_or_404(models.Calendar, pk=calendar_id)

    try:
        style = models.ColorSet.objects.get(pk=style_id).to_style()
        layout = models.Layout.objects.get(pk=layout_id).to_pdf_layout()

    except (ValueError, IndexError, models.ColorSet.DoesNotExist, models.Layout.DoesNotExist) as exc:
        return HttpResponseBadRequest(str(exc))

    date_letter_map = cal.get_date_letter_map()
    label_map = cal.get_arbitrary_labels()

    buf = BytesIO()
    pdf_canvas = canvas.Canvas(buf, pagesize=(layout.width, layout.height))

    if request.user.is_authenticated:
        pdf_canvas.setAuthor(str(request.user))

    pdf_canvas.setTitle(cal.title)
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
    return FileResponse(buf, filename=f"{cal.title} - All Months.pdf")


@permission_required(VIEW_CALENDAR_PERMISSION)
def pdf_one_page(request, calendar_id: int, style_id: int, layout_id: int):
    """Generate a one page PDF with all calendars on it"""

    cal = get_object_or_404(models.Calendar, pk=calendar_id)

    try:
        db_style = models.ColorSet.objects.get(pk=style_id)
        db_layout = models.Layout.objects.get(pk=layout_id)

        assert isinstance(db_style, models.ColorSet)
        assert isinstance(db_layout, models.Layout)

        style = db_style.to_style()
        layout = db_layout.to_pdf_layout()

    except (ValueError, IndexError, models.ColorSet.DoesNotExist, models.Layout.DoesNotExist) as exc:
        return HttpResponseBadRequest(str(exc))

    date_letter_map = cal.get_date_letter_map()
    label_map = cal.get_arbitrary_labels()

    all_months = set()
    for used_date in date_letter_map | label_map:
        all_months.add((used_date.year, used_date.month))

    row_count = math.ceil(len(all_months)/ONE_PAGE_PDF_COL_COUNT)
    layouts = layout.subdivide(row_count, ONE_PAGE_PDF_COL_COUNT)

    title_font_sizes: List[float] = []
    for year, month in all_months:
        title = date(year, month, 1).strftime("%B %Y")
        font_size = pdf.get_maximum_width(title, layouts[0].outer_width / 2, layout.title_font_name)
        title_font_sizes.append(font_size)

    title_font_size = min(title_font_sizes)

    buf = BytesIO()
    pdf_canvas = canvas.Canvas(buf, pagesize=(layout.width, layout.height))

    if request.user.is_authenticated:
        pdf_canvas.setAuthor(str(request.user))

    pdf_canvas.setTitle(cal.title)
    pdf_canvas.setCreator("Rectory Apps System")
    pdf_canvas.setSubject("Calendar")

    for i, (year, month) in enumerate(sorted(all_months)):
        layout = layouts[i]
        layout.title_font_size_override = title_font_size

        start_date = date(year, month, 1)
        _, end_day = calendar.monthrange(year, month)
        end_date = date(year, month, end_day)

        grid_generator = grids.CalendarGridGenerator(date_letter_map, label_map, start_date, end_date)
        grid = grid_generator.get_grid()

        generator = pdf.CalendarGenerator(pdf_canvas, grid, style, layout, minimum_row_count_calculation=5)
        generator.draw()

    pdf_canvas.save()

    buf.seek(0)
    return FileResponse(buf, filename=f"{cal.title} - All Months.pdf")


def _parse_date(val: Union[str, date]) -> date:
    if isinstance(val, date):
        return val

    parts = val.split("-")
    int_parts = (int(p) for p in parts)

    return date(*int_parts)
