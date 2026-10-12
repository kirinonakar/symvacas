"""Validate regular calendar observations and extend their dates without drift."""
import calendar
from datetime import date, timedelta
from calc_shared import MathError, require
from calc_advanced_common import integer


def time_calendar(raw, size, horizon):
    require(isinstance(raw, (list, tuple)) and len(raw) == size,
            'Dates must have one value per observation')
    years_only = all(not isinstance(v, (list, tuple)) for v in raw)
    dates = []
    try:
        for item in raw:
            if years_only:
                parts = [integer(item, 1, 9999), 1, 1]
            else:
                require(isinstance(item, (list, tuple)) and len(item) == 3,
                        'Dates must be years or [year,month,day] rows')
                parts = [integer(v, lo, hi) for v, lo, hi in zip(item, (1, 1, 1), (9999, 12, 31))]
            dates.append(date(*parts))
    except ValueError:
        raise MathError('Enter valid calendar dates')
    require(all(a < b for a, b in zip(dates, dates[1:])),
            'Dates must be strictly increasing without duplicates')
    first = dates[0]
    months = [(value.year-first.year)*12+value.month-first.month for value in dates]
    month_step = months[1]
    month_end = all(value.day == calendar.monthrange(value.year, value.month)[1] for value in dates)

    def add_months(offset):
        index = first.year*12+first.month-1+offset
        year, month = divmod(index, 12)
        month += 1
        last = calendar.monthrange(year, month)[1]
        return date(year, month, last if month_end else min(first.day, last))

    regular_months = month_step > 0 and months == [i*month_step for i in range(size)] and \
                     all(add_months(i*month_step) == value for i, value in enumerate(dates))
    if regular_months:
        frequency = 'Yearly' if month_step % 12 == 0 else 'Quarterly' if month_step % 3 == 0 else 'Monthly'
        step = month_step//12 if frequency == 'Yearly' else month_step//3 if frequency == 'Quarterly' else month_step
        future = lambda i: add_months(i*month_step)
    else:
        days = [(value-first).days for value in dates]
        day_step = days[1]
        require(days == [i*day_step for i in range(size)],
                'Dates must have regular yearly, monthly or day intervals; fill missing periods first')
        frequency = 'Weekly' if day_step % 7 == 0 else 'Daily'
        step = day_step//7 if frequency == 'Weekly' else day_step
        future = lambda i: first+timedelta(days=i*day_step)
    try:
        extended = dates + [future(i) for i in range(size, size+horizon)]
    except (ValueError, OverflowError):
        raise MathError('Forecast dates exceed the supported calendar range')
    labels = [str(value.year) if years_only else value.isoformat() for value in extended]
    ticks = [str(value.year) if frequency == 'Yearly' else value.strftime('%Y-%m')
             if frequency in ('Monthly', 'Quarterly') else label for value, label in zip(extended, labels)]
    return {'labels': labels, 'ticks': ticks, 'frequency': frequency, 'step': step}
