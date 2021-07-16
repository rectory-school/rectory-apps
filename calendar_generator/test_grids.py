"""Tests for grid generation"""

from datetime import date

from . import grids


def test_grid_generation():
    """Test the generation of the May 2021 calendar grid"""

    days = {
        date(2021, 3, 1): "O",
        date(2021, 3, 2): "B",
        date(2021, 3, 3): "O",
        date(2021, 3, 4): "B",
        date(2021, 3, 15): "O",
        date(2021, 3, 16): "B",
        date(2021, 3, 17): "O",
        date(2021, 3, 18): "B",
        date(2021, 3, 19): "O",
        date(2021, 3, 22): "B",
        date(2021, 3, 23): "O",
        date(2021, 3, 24): "B",
        date(2021, 3, 25): "O",
        date(2021, 3, 26): "B",
        date(2021, 3, 29): "O",
        date(2021, 3, 30): "B",
        date(2021, 3, 31): "O",
    }

    expected_headers = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    expected_grid = [
        [
            grids.GridItem(date(2021, 3, 1), "O"),
            grids.GridItem(date(2021, 3, 2), "B"),
            grids.GridItem(date(2021, 3, 3), "O"),
            grids.GridItem(date(2021, 3, 4), "B"),
            grids.GridItem(date(2021, 3, 5), None),
        ],
        [
            grids.GridItem(date(2021, 3, 8), None),
            grids.GridItem(date(2021, 3, 9), None),
            grids.GridItem(date(2021, 3, 10), None),
            grids.GridItem(date(2021, 3, 11), None),
            grids.GridItem(date(2021, 3, 12), None),
        ],
        [
            grids.GridItem(date(2021, 3, 15), "O"),
            grids.GridItem(date(2021, 3, 16), "B"),
            grids.GridItem(date(2021, 3, 17), "O"),
            grids.GridItem(date(2021, 3, 18), "B"),
            grids.GridItem(date(2021, 3, 19), "O"),
        ],
        [
            grids.GridItem(date(2021, 3, 22), "B"),
            grids.GridItem(date(2021, 3, 23), "O"),
            grids.GridItem(date(2021, 3, 24), "B"),
            grids.GridItem(date(2021, 3, 25), "O"),
            grids.GridItem(date(2021, 3, 26), "B"),
        ],
        [
            grids.GridItem(date(2021, 3, 29), "O"),
            grids.GridItem(date(2021, 3, 30), "B"),
            grids.GridItem(date(2021, 3, 31), "O"),
            None,
            None,
        ]
    ]

    expected = grids.CalendarGrid(headers=expected_headers, grid=expected_grid)

    generator = grids.CalendarGridGenerator(date_letter_map=days, year=2021, month=3, week_start=6)
    actual = generator.get_grid()

    assert actual == expected


def test_last_empty():
    """Test that, in certain circumstances, the last grid row won't be empty"""

    # This was the October 2021 mock calendar, which was showing up with a phantom last fully empty row
    # Likely this is because of the calendar generating the row for the weekend, but us excluding the weekend

    days = {
        date(2021, 10, 1): "A",
        date(2021, 10, 4): "B",
        date(2021, 10, 5): "A",
        date(2021, 10, 6): "B",
        date(2021, 10, 7): "A",
        date(2021, 10, 8): "B",
        date(2021, 10, 11): "A",
        date(2021, 10, 12): "B",
        date(2021, 10, 13): "A",
        date(2021, 10, 14): "B",
        date(2021, 10, 15): "A",
        date(2021, 10, 18): "B",
        date(2021, 10, 19): "A",
        date(2021, 10, 20): "B",
        date(2021, 10, 21): "A",
        date(2021, 10, 22): "B",
        date(2021, 10, 25): "A",
        date(2021, 10, 26): "B",
        date(2021, 10, 27): "A",
        date(2021, 10, 28): "B",
        date(2021, 10, 29): "A",
    }
    expected_headers = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    expected_grid = [
        [
            None,
            None,
            None,
            None,
            grids.GridItem(date(2021, 10, 1), "A"),
        ],
        [
            grids.GridItem(date(2021, 10, 4), "B"),
            grids.GridItem(date(2021, 10, 5), "A"),
            grids.GridItem(date(2021, 10, 6), "B"),
            grids.GridItem(date(2021, 10, 7), "A"),
            grids.GridItem(date(2021, 10, 8), "B"),
        ],
        [
            grids.GridItem(date(2021, 10, 11), "A"),
            grids.GridItem(date(2021, 10, 12), "B"),
            grids.GridItem(date(2021, 10, 13), "A"),
            grids.GridItem(date(2021, 10, 14), "B"),
            grids.GridItem(date(2021, 10, 15), "A"),
        ],
        [
            grids.GridItem(date(2021, 10, 18), "B"),
            grids.GridItem(date(2021, 10, 19), "A"),
            grids.GridItem(date(2021, 10, 20), "B"),
            grids.GridItem(date(2021, 10, 21), "A"),
            grids.GridItem(date(2021, 10, 22), "B"),
        ],
        [
            grids.GridItem(date(2021, 10, 25), "A"),
            grids.GridItem(date(2021, 10, 26), "B"),
            grids.GridItem(date(2021, 10, 27), "A"),
            grids.GridItem(date(2021, 10, 28), "B"),
            grids.GridItem(date(2021, 10, 29), "A"),
        ]
    ]

    expected = grids.CalendarGrid(headers=expected_headers, grid=expected_grid)

    generator = grids.CalendarGridGenerator(date_letter_map=days, year=2021, month=10, week_start=6)
    actual = generator.get_grid()

    assert actual == expected
