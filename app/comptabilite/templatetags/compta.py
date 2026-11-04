from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def montant(value):
    if value is None or value == "":
        return ""
    s = f"{Decimal(value):,.2f}"
    return s.replace(",", "\u202f").replace(".", ",")
