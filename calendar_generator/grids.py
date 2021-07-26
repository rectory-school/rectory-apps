"""Grid generators for calendars"""

from dataclasses import dataclass
from datetime import date
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
    is_label: bool = False


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

    year: int
    month: int
    week_start: int = 6

    custom_title: Optional[str] = None
    perform_date_range_check: bool = True

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

        # Monday, Tuesday, Wednesday - just those weekdays that were used in this calendar
        used_headers = [HEADERMAPPING[weekday] for weekday in cal.iterweekdays() if weekday in used_weekdays]

        out = CalendarGrid(headers=used_headers, grid=[], title=self.title)

        # This may have the previous or next month on it
        full_grid = cal.monthdatescalendar(self.year, self.month)

        def get_entry(date_val: date) -> Optional[GridItem]:
            """
            Get the entry for this item in the calendar grid
            Will either be a grid item, or a None if it's out of our month range
            """

            if self.perform_date_range_check:
                if date_val.year != self.year:
                    return None

                if date_val.month != self.month:
                    return None

            if date_val in self.label_map:
                return GridItem(date_val, self.label_map[date_val], is_label=True)

            return GridItem(date_val, self.date_letter_map.get(date_val))

        for week in full_grid:
            # Filter to just items that are within our scope for weekdays, so we remove unused columns
            weekday_filtered_week = (day for day in week if day.weekday() in used_weekdays)

            week_entries = [get_entry(d) for d in weekday_filtered_week]
            if week_entries != [None]*len(used_weekdays):
                # The calendar grid can generate a phantom unused row over an unused day - don't keep it
                out.grid.append(week_entries)

        return out

    @property
    def title(self) -> str:
        """Get the title of a calendar with this grid"""

        sample_date = date(self.year, self.month, 1)
        return sample_date.strftime("%B %Y")
