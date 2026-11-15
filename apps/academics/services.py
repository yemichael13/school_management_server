"""Academic date and lifecycle services.

Dates are persisted as Gregorian ``date`` values. Ethiopian-calendar values
are derived at the API boundary so reporting and storage remain unambiguous.
"""

from datetime import date, timedelta


def gregorian_to_ethiopian(value: date) -> dict[str, int]:
    """Convert a Gregorian date to an Ethiopian calendar date.

    The conversion uses the Ethiopian New Year boundary and returns a
    serializable mapping rather than a second date type. Gregorian dates are
    retained as the source of truth in the database.
    """
    new_year = date(value.year, 9, 11)
    if value < new_year:
        ethiopian_year = value.year - 8
        new_year = date(value.year - 1, 9, 11)
    else:
        ethiopian_year = value.year - 7
    elapsed_days = (value - new_year).days
    ethiopian_month = (elapsed_days // 30) + 1
    ethiopian_day = (elapsed_days % 30) + 1
    return {
        'year': ethiopian_year,
        'month': ethiopian_month,
        'day': ethiopian_day,
        'iso': f'{ethiopian_year:04d}-{ethiopian_month:02d}-{ethiopian_day:02d}',
    }


def date_range_is_valid(start: date, end: date) -> bool:
    return end >= start


def semester_is_within_academic_year(academic_year, start: date, end: date) -> bool:
    return (
        date_range_is_valid(start, end)
        and start >= academic_year.start_date
        and end <= academic_year.end_date
    )


def school_structure_summary(school):
    """Return lightweight counts used by administrative dashboards."""
    return {
        'school_id': str(school.id),
        'school_code': school.code,
        'school_name': school.name,
        'academic_year_count': school.academic_years.count(),
        'subject_count': school.subjects.filter(is_active=True).count(),
    }
