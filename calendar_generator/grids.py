"""Grid generators for calendars"""

import math
from dataclasses import dataclass
from datetime import date, timedelta
import calendar
from typing import Optional, List, Set, Dict

HEADERMAPPING = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday',
}


@dataclass
class GridItem:
    """A date/letter pair in a grid"""

    date: date
    letter: Optional[str]
    label: Optional[str]


@dataclass
class CalendarGrid:
    """Everything that is needed to draw a calendar grid"""

    title: str
    headers: List[str]  # Monday, Tuesday, Wednesday
    grid: List[List[Optional[GridItem]]]  # 2d calendar view of grid items


@dataclass
class CalendarGridGenerator:
    """A generator that makes a calendar grid"""

    date_letter_map: Dict[date, str]
    label_map: Dict[date, str]

    start_date: date
    end_date: date

    week_start: int = 6

    custom_title: Optional[str] = None

    def get_used_weekdays(self) -> Set[int]:
        """The weekdays that have been used by all the dates together"""

        out = set()

        for letter_date in self.date_letter_map.keys():
            out.add(letter_date.weekday())

        for label_date in self.label_map.keys():
            out.add(label_date.weekday())

        return out

    def get_grid(self) -> CalendarGrid:
        """The 2d grid calendar view of days and times"""

        used_weekdays = self.get_used_weekdays()

        # All grid items and headers will be referenced off the calendar object, for start of week consistency
        cal = calendar.Calendar(firstweekday=self.week_start)

        # The weekdays as they should be in columns across our calendar
        ordered_weekdays = [weekday for weekday in cal.iterweekdays() if weekday in used_weekdays]

        # Monday, Tuesday, Wednesday - just those weekdays that were used in this calendar
        used_headers = [HEADERMAPPING[weekday] for weekday in ordered_weekdays]

        out = CalendarGrid(headers=used_headers, grid=[], title=self.title)

        # Walk backwards until we get our first weekday
        target_weekday = ordered_weekdays[0]
        internal_start_date = self.start_date

        while internal_start_date.weekday() != target_weekday:
            internal_start_date -= timedelta(days=1)

        total_weeks = math.ceil((self.end_date - internal_start_date).days / 7)
        full_grid = []
        for week_index in range(total_weeks):
            week_start = internal_start_date + timedelta(days=week_index*7)
            row = []
            for day_index in range(len(used_weekdays)):
                cell_date = week_start + timedelta(days=day_index)

                if cell_date >= self.start_date and cell_date <= self.end_date:
                    row.append(cell_date)
                else:
                    row.append(None)

            full_grid.append(row)

        # Now we have a date corresponding to the actual first day that might be on our calendar,
        # even though we might not display that date because it's outside of our range

        # Create the grid we're going to be using

        def get_entry(date_val: date) -> Optional[GridItem]:
            """
            Get the entry for this item in the calendar grid
            Will either be a grid item, or a None if it's out of our month range
            """

            letter = self.date_letter_map.get(date_val)
            label = self.label_map.get(date_val)

            return GridItem(date_val, letter, label)

        for week in full_grid:
            week_entries = [get_entry(d) for d in week]
            if week_entries != [None]*len(used_weekdays):
                # The calendar grid can generate a phantom unused row over an unused day - don't keep it
                out.grid.append(week_entries)

        return out

    @property
    def title(self) -> str:
        """Get the title of a calendar with this grid"""

        if self.custom_title:
            return self.custom_title

        if self.start_date.year == self.end_date.year and self.start_date.month == self.end_date.month:
            sample_date = date(self.start_date.year, self.end_date.month, 1)

            return sample_date.strftime("%B %Y")

        start_date_str = self.start_date.strftime("%b %d, %Y")
        end_date_str = self.end_date.strftime("%b %d, %Y")

        return f"{start_date_str} to {end_date_str}"
