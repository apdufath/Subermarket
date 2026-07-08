import re
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import OrderItem, Product

SKU_PATTERN = re.compile(r'SKU:\s*([A-Z0-9-]+)', re.IGNORECASE)


class OrderProcessingError(Exception):
    """Raised when an order cannot be processed due to validation or stock issues."""


def extract_sku(description):
    if not description:
        return '—'
    match = SKU_PATTERN.search(description)
    return match.group(1) if match else '—'


def parse_decimal(value, default='0.00'):
    try:
        return Decimal(str(value or default))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def parse_product_quantities(product_ids, post_data):
    """Build a dict of product_id -> quantity from POST data."""
    quantities = {}
    for p_id in product_ids:
        qty_str = post_data.get(f'quantity_{p_id}', '0')
        try:
            qty = int(qty_str)
        except (TypeError, ValueError):
            qty = 0
        if qty > 0:
            quantities[str(p_id)] = qty
    return quantities


@transaction.atomic
def create_order_with_items(order, product_quantities):
    """
    Create order line items, deduct stock, and return the merchandise subtotal.
    Rolls back the entire transaction on any error.
    """
    subtotal = Decimal('0.00')
    items_added = 0

    for p_id, qty in product_quantities.items():
        if qty <= 0:
            continue

        product = Product.objects.select_for_update().get(pk=p_id)
        if product.stock < qty:
            raise OrderProcessingError(
                f'Insufficient stock available for {product.name}. '
                f'Available: {product.stock}.'
            )

        line_subtotal = product.price * qty
        product.stock -= qty
        product.save(update_fields=['stock'])

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=qty,
            price=product.price,
            subtotal=line_subtotal,
        )
        subtotal += line_subtotal
        items_added += 1

    if items_added == 0:
        raise OrderProcessingError('Please enter a valid quantity for at least one product.')

    return subtotal


def calculate_grand_total(subtotal, tax=Decimal('0.00'), discount=Decimal('0.00')):
    grand_total = subtotal + tax - discount
    return max(grand_total, Decimal('0.00'))
