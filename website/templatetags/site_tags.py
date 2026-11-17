from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def money(value):
    """£1,240 for whole pounds, £12.50 otherwise."""
    if value in (None, ""):
        value = 0
    value = Decimal(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    text = f"{value:,.0f}" if value == value.to_integral_value() else f"{value:,.2f}"
    return f"{sign}£{text}"
