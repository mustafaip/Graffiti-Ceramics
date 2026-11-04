# -*- coding: utf-8 -*-
"""Pure conversion maths (no Odoo imports, so it is trivially testable)."""
import math

RATIO_DIGITS = 6  # absorbs float noise, e.g. 50.4 / 1.44 = 35.00000000000001


def _ceil_ratio(numerator, denominator):
    return int(math.ceil(round(numerator / denominator, RATIO_DIGITS)))


def box_area(sqm_per_piece, pieces_per_box):
    return (sqm_per_piece or 0.0) * (pieces_per_box or 0)


def normalize(driver, value, sqm_per_piece, pieces_per_box, qty_digits=2):
    """Return {'qty', 'boxes', 'pieces'} for the field the user just changed.

    driver: 'qty' (SQM), 'boxes' or 'pieces'. Quantities are always rounded UP
    to a whole number of boxes. Returns None when the factors are missing or
    when there is nothing to round (negative quantity, e.g. a return).
    """
    area = box_area(sqm_per_piece, pieces_per_box)
    if area <= 0 or (pieces_per_box or 0) <= 0:
        return None
    value = value or 0.0
    if driver == 'qty':
        if value < 0:
            return None
        boxes = _ceil_ratio(value, area) if value > 0 else 0
    elif driver == 'boxes':
        boxes = max(int(math.ceil(round(value, RATIO_DIGITS))), 0)
    elif driver == 'pieces':
        boxes = _ceil_ratio(value, pieces_per_box) if value > 0 else 0
    else:
        raise ValueError(driver)
    return {
        'qty': round(boxes * area, qty_digits),
        'boxes': boxes,
        'pieces': boxes * pieces_per_box,
    }
