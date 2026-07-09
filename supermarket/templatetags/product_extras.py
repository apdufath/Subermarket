from datetime import timedelta
from decimal import Decimal

from django import template
from django.db.models import F, Sum
from django.utils import timezone

from supermarket.models import Customer, Order, OrderItem, Product
from supermarket.order_utils import extract_sku as _extract_sku

register = template.Library()


@register.filter
def extract_sku(description):
    """Extract SKU code from product description, if present."""
    return _extract_sku(description)


def _merchandise_subtotal(order):
    return sum((item.subtotal for item in order.items.all()), Decimal('0.00'))


@register.filter
def order_merchandise_subtotal(order):
    """Sum line-item subtotals for invoice display."""
    return _merchandise_subtotal(order)


@register.filter
def order_adjustment(order):
    """Difference between grand total and merchandise subtotal (tax/discount)."""
    return order.total_amount - _merchandise_subtotal(order)


@register.filter
def abs_value(value):
    """Return absolute value for invoice display."""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value


@register.filter
def stock_status(stock):
    """Return stock status label for badge display."""
    if stock <= 0:
        return 'out'
    if stock <= 10:
        return 'low'
    return 'in'


@register.simple_tag
def get_sales_overview():
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    orders = Order.objects.all()
    return {
        'total': orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'today': orders.filter(date_ordered__gte=today_start).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'week': orders.filter(date_ordered__gte=week_start).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'month': orders.filter(date_ordered__gte=month_start).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
    }


@register.simple_tag
def get_top_selling_products(limit=5):
    rows = (
        OrderItem.objects
        .values('product')
        .annotate(
            units_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('price')),
        )
        .order_by('-units_sold')[:limit]
    )

    results = []
    for row in rows:
        product = Product.objects.filter(pk=row['product']).select_related('category').first()
        if not product:
            continue
        results.append({
            'product': product,
            'units_sold': row['units_sold'] or 0,
            'revenue': row['revenue'] or Decimal('0.00'),
        })
    return results


@register.simple_tag
def get_latest_customers(limit=5):
    return Customer.objects.order_by('-id')[:limit]