"""Tests for grid generation"""

from datetime import date

from . import grids


def test_grid_jan_2022():
    """A specific unit test for January 31st, 2022 not showing up"""

    days = {
        date(2022, 1, 5): "E",
        date(2022, 1, 6): "C",
        date(2022, 1, 7): "A",
        date(2022, 1, 10): "F",
        date(2022, 1, 11): "D",
        date(2022, 1, 12): "B",
        date(2022, 1, 13): "G",
        date(2022, 1, 14): "E",
        date(2022, 1, 18): "C",
        date(2022, 1, 19): "A",
        date(2022, 1, 20): "F",
        date(2022, 1, 21): "D",
        date(2022, 1, 24): "B",
        date(2022, 1, 25): "G",
        date(2022, 1, 26): "E",
        date(2022, 1, 27): "C",
        date(2022, 1, 28): "A",
        date(2022, 1, 31): "F",
    }

    expected_headers = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    expected_grid = [
        [
            grids.GridItem(date(2022, 1, 3), None),
            grids.GridItem(date(2022, 1, 4), None),
            grids.GridItem(date(2022, 1, 5), "E"),
            grids.GridItem(date(2022, 1, 6), "C"),
            grids.GridItem(date(2022, 1, 7), "A"),
        ],
        [
            grids.GridItem(date(2022, 1, 10), "F"),
            grids.GridItem(date(2022, 1, 11), "D"),
            grids.GridItem(date(2022, 1, 12), "B"),
            grids.GridItem(date(2022, 1, 13), "G"),
            grids.GridItem(date(2022, 1, 14), "E"),
        ],
        [
            grids.GridItem(date(2022, 1, 17), None),
            grids.GridItem(date(2022, 1, 18), "C"),
            grids.GridItem(date(2022, 1, 19), "A"),
            grids.GridItem(date(2022, 1, 20), "F"),
            grids.GridItem(date(2022, 1, 21), "D"),
        ],
        [
            grids.GridItem(date(2022, 1, 24), "B"),
            grids.GridItem(date(2022, 1, 25), "G"),
            grids.GridItem(date(2022, 1, 26), "E"),
            grids.GridItem(date(2022, 1, 27), "C"),
            grids.GridItem(date(2022, 1, 28), "A"),
        ],
        [
            grids.GridItem(date(2022, 1, 31), "F"),
            None,
            None,
            None,
            None,
        ],
    ]

    expected = grids.CalendarGrid(title="January 2022", headers=expected_headers, grid=expected_grid)

    generator = grids.CalendarGridGenerator(
        date_letter_map=days, label_map={},
        start_date=date(2022, 1, 1),
        end_date=date(2022, 1, 31))

    actual = generator.get_grid()

    assert actual == expected


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

    expected = grids.CalendarGrid(title="March 2021", headers=expected_headers, grid=expected_grid)

    generator = grids.CalendarGridGenerator(
        date_letter_map=days, label_map={},
        start_date=date(2021, 3, 1),
        end_date=date(2021, 3, 31))
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

    expected = grids.CalendarGrid(title="October 2021", headers=expected_headers, grid=expected_grid)

    generator = grids.CalendarGridGenerator(
        date_letter_map=days, label_map={},
        start_date=date(2021, 10, 1),
        end_date=date(2021, 10, 29),
        week_start=6)
    actual = generator.get_grid()

    assert actual == expected
