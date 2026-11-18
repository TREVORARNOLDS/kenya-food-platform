from datetime import date
from itertools import pairwise

import numpy as np


def _month_index(d: date) -> int:
    return d.year * 12 + d.month


def volatility_stats(series: list[tuple[date, float]]) -> dict:
    """Volatility measures for a monthly price series, sorted by month.

    - coefficient_of_variation_pct: spread of monthly averages relative to their mean.
    - mean_abs_monthly_change_pct / monthly_change_std_pct: month-over-month changes,
      computed only between consecutive calendar months, so gaps never inflate them.
    Measures that need more data than available are None.
    """
    months = len(series)
    stats = {
        "months": months,
        "mean_price": None,
        "coefficient_of_variation_pct": None,
        "mean_abs_monthly_change_pct": None,
        "monthly_change_std_pct": None,
    }
    if months == 0:
        return stats

    values = np.array([v for _, v in series], dtype=float)
    mean = float(values.mean())
    stats["mean_price"] = mean
    if months < 3:
        return stats

    if mean > 0:
        stats["coefficient_of_variation_pct"] = float(values.std(ddof=1) / mean * 100)

    changes = [
        (v2 - v1) / v1 * 100
        for (m1, v1), (m2, v2) in pairwise(series)
        if _month_index(m2) - _month_index(m1) == 1 and v1 > 0
    ]
    if changes:
        stats["mean_abs_monthly_change_pct"] = float(np.mean(np.abs(changes)))
    if len(changes) >= 2:
        stats["monthly_change_std_pct"] = float(np.std(changes, ddof=1))
    return stats
