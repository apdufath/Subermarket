import re
from datetime import timedelta
from decimal import Decimal

from django import template
from django.db.models import F, Sum
from django.utils import timezone

from supermarket.models import Customer, Order, OrderItem, Product

register = template.Library()
SKU_PATTERN = re.compile(r'SKU:\s*([A-Z0-9-]+)', re.IGNORECASE)


@register.filter
def extract_sku(description):
    """Extract SKU code from product description, if present."""
    if not description:
        return '—'
    match = SKU_PATTERN.search(description)
    return match.group(1) if match else '—'


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