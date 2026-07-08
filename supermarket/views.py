from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from uuid import uuid4
from .forms import SignUpForm
from .models import Category, Supplier, Product, Customer, Order, OrderItem, UserProfile
from .order_utils import (
    OrderProcessingError,
    calculate_grand_total,
    create_order_with_items,
    extract_sku,
    parse_decimal,
    parse_product_quantities,
)
from .utils import validate_product_image, remove_product_image


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')
        if remember_me:
            self.request.session.set_expiry(1209600)  # 2 weeks
        else:
            self.request.session.set_expiry(0)  # End session when browser closes
        return super().form_valid(form)


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['full_name'].strip()
            name_parts = full_name.split(None, 1)

            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=name_parts[0],
                last_name=name_parts[1] if len(name_parts) > 1 else '',
            )
            UserProfile.objects.create(
                user=user,
                phone=form.cleaned_data['phone'].strip(),
            )
            login(request, user)
            messages.success(request, 'Welcome to Star Supermarket! Your account has been created successfully.')
            return redirect('dashboard')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


@login_required(login_url='login')
def dashboard(request):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()
    total_customers = Customer.objects.count()
    total_orders = Order.objects.count()

    low_stock_products = Product.objects.filter(stock__lt=10).select_related('category')
    recent_orders = Order.objects.select_related('customer').order_by('-date_ordered')[:5]

    stat_cards = [
        {
            'title': 'Products',
            'subtitle': 'Total Products',
            'count': total_products,
            'url_name': 'product_list',
            'icon': 'bi-box-seam',
            'theme': 'stat-products',
            'delay': 0,
        },
        {
            'title': 'Categories',
            'subtitle': 'Total Categories',
            'count': total_categories,
            'url_name': 'category_list',
            'icon': 'bi-tags',
            'theme': 'stat-categories',
            'delay': 80,
        },
        {
            'title': 'Suppliers',
            'subtitle': 'Total Suppliers',
            'count': total_suppliers,
            'url_name': 'supplier_list',
            'icon': 'bi-truck',
            'theme': 'stat-suppliers',
            'delay': 160,
        },
        {
            'title': 'Customers',
            'subtitle': 'Total Customers',
            'count': total_customers,
            'url_name': 'customer_list',
            'icon': 'bi-people',
            'theme': 'stat-customers',
            'delay': 240,
        },
        {
            'title': 'Orders',
            'subtitle': 'Total Orders',
            'count': total_orders,
            'url_name': 'order_list',
            'icon': 'bi-cart-check',
            'theme': 'stat-orders',
            'delay': 320,
        },
    ]

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'total_customers': total_customers,
        'total_orders': total_orders,
        'stat_cards': stat_cards,
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
    }
    return render(request, 'supermarket/dashboard.html', context)


@login_required(login_url='login')
def category_list(request):
    search_query = request.GET.get('search', '')
    categories = Category.objects.all().order_by('id')

    if search_query:
        categories = categories.filter(name__icontains=search_query)

    paginator = Paginator(categories, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'supermarket/category_list.html', {'page_obj': page_obj, 'search_query': search_query})


@login_required(login_url='login')
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            Category.objects.create(name=name, description=description or None)
            messages.success(request, "Category saved successfully.")
            return redirect('category_list')
        messages.error(request, "Please enter a category name.")
    return render(request, 'supermarket/category_form.html')


@login_required(login_url='login')
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, "Please enter a category name.")
            return render(request, 'supermarket/category_form.html', {'category': category})
        category.name = name
        category.description = request.POST.get('description', '').strip() or None
        category.save()
        messages.success(request, "Category updated successfully.")
        return redirect('category_list')
    return render(request, 'supermarket/category_form.html', {'category': category})


@login_required(login_url='login')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted successfully.")
        return redirect('category_list')
    return render(request, 'supermarket/category_confirm_delete.html', {'category': category})


@login_required(login_url='login')
def supplier_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        suppliers = Supplier.objects.filter(
            Q(company_name__icontains=search_query) |
            Q(phone__icontains=search_query)
        ).order_by('-id')
    else:
        suppliers = Supplier.objects.all().order_by('-id')

    paginator = Paginator(suppliers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'supermarket/supplier_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
    })


@login_required(login_url='login')
def supplier_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        if not name:
            messages.error(request, "Please enter a company name.")
        elif not phone:
            messages.error(request, "Please enter a phone number.")
        elif not email:
            messages.error(request, "Please enter an email address.")
        elif not address:
            messages.error(request, "Please enter an address.")
        else:
            Supplier.objects.create(
                company_name=name,
                contact_person=name,
                phone=phone,
                email=email,
                address=address,
            )
            messages.success(request, "Supplier added successfully.")
            return redirect('supplier_list')
    return render(request, 'supermarket/supplier_form.html')


@login_required(login_url='login')
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        if not name or not phone or not email or not address:
            messages.error(request, "All supplier fields are required.")
            return render(request, 'supermarket/supplier_form.html', {'supplier': supplier})

        supplier.company_name = name
        supplier.contact_person = name
        supplier.phone = phone
        supplier.email = email
        supplier.address = address
        supplier.save()
        messages.success(request, "Supplier updated successfully.")
        return redirect('supplier_list')
    return render(request, 'supermarket/supplier_form.html', {'supplier': supplier})


@login_required(login_url='login')
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, "Supplier deleted successfully.")
        return redirect('supplier_list')
    return render(request, 'supermarket/supplier_confirm_delete.html', {'supplier': supplier})


@login_required(login_url='login')
def product_list(request):
    search_query = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category', '').strip()
    sort_by = request.GET.get('sort', 'newest')

    products = Product.objects.select_related('category', 'supplier').all()

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_filter.isdigit():
        products = products.filter(category_id=int(category_filter))

    sort_options = {
        'newest': '-id',
        'oldest': 'id',
        'name_asc': 'name',
        'name_desc': '-name',
        'price_asc': 'price',
        'price_desc': '-price',
        'stock_asc': 'stock',
        'stock_desc': '-stock',
    }
    products = products.order_by(sort_options.get(sort_by, '-id'))

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'supermarket/product_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'categories': Category.objects.all().order_by('name'),
        'total_results': paginator.count,
    })


@login_required(login_url='login')
def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related('category', 'supplier'),
        pk=pk,
    )
    return render(request, 'supermarket/product_detail.html', {'product': product})


def _product_form_context(product=None, categories=None, suppliers=None):
    return {
        'product': product,
        'categories': categories if categories is not None else Category.objects.all(),
        'suppliers': suppliers if suppliers is not None else Supplier.objects.all(),
    }


def _handle_product_image(request, product=None):
    """Process image upload/removal. Returns (success, product_or_none)."""
    remove_image = request.POST.get('remove_image') == 'on'
    new_image = request.FILES.get('image')

    if new_image:
        is_valid, error = validate_product_image(new_image)
        if not is_valid:
            messages.error(request, error)
            return False, product

    if product and remove_image:
        remove_product_image(product)
    elif new_image:
        if product and product.image:
            product.image.delete(save=False)
        if product:
            product.image = new_image
        return True, new_image

    return True, product.image if product else new_image


@login_required(login_url='login')
def product_create(request):
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        supplier_id = request.POST.get('supplier')
        price = request.POST.get('selling_price')
        cost_price = request.POST.get('cost_price') or 0
        quantity = request.POST.get('stock')
        barcode = request.POST.get('barcode', '').strip()
        description = request.POST.get('description', '').strip()
        image = request.FILES.get('image')

        if not name:
            messages.error(request, "Please enter a product name.")
        elif not category_id:
            messages.error(request, "Please select a category.")
        elif not price:
            messages.error(request, "Please enter a selling price.")
        elif not quantity:
            messages.error(request, "Please enter stock quantity.")
        else:
            is_valid, error = validate_product_image(image)
            if not is_valid:
                messages.error(request, error)
                return render(request, 'supermarket/product_form.html', _product_form_context(
                    categories=categories, suppliers=suppliers,
                ))

            category = get_object_or_404(Category, id=category_id)
            supplier = get_object_or_404(Supplier, id=supplier_id) if supplier_id else None

            if not barcode:
                barcode = f"AUTO-{uuid4().hex[:12].upper()}"
            elif Product.objects.filter(barcode=barcode).exists():
                messages.error(request, "A product with this barcode already exists.")
                return render(request, 'supermarket/product_form.html', _product_form_context(
                    categories=categories, suppliers=suppliers,
                ))

            Product.objects.create(
                name=name,
                category=category,
                supplier=supplier,
                price=price,
                cost_price=cost_price,
                stock=quantity,
                barcode=barcode,
                description=description or None,
                image=image,
            )
            messages.success(request, "Product added successfully.")
            return redirect('product_list')

    return render(request, 'supermarket/product_form.html', _product_form_context(
        categories=categories, suppliers=suppliers,
    ))


@login_required(login_url='login')
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        supplier_id = request.POST.get('supplier')
        barcode = request.POST.get('barcode', '').strip()

        if not name or not category_id:
            messages.error(request, "Product name and category are required.")
            return render(request, 'supermarket/product_form.html', _product_form_context(
                product=product, categories=categories, suppliers=suppliers,
            ))

        if not barcode:
            barcode = product.barcode or f"AUTO-{uuid4().hex[:12].upper()}"
        elif Product.objects.filter(barcode=barcode).exclude(pk=product.pk).exists():
            messages.error(request, "A product with this barcode already exists.")
            return render(request, 'supermarket/product_form.html', _product_form_context(
                product=product, categories=categories, suppliers=suppliers,
            ))

        image_ok, _ = _handle_product_image(request, product)
        if not image_ok:
            return render(request, 'supermarket/product_form.html', _product_form_context(
                product=product, categories=categories, suppliers=suppliers,
            ))

        product.name = name
        product.category = get_object_or_404(Category, id=category_id)
        product.supplier = get_object_or_404(Supplier, id=supplier_id) if supplier_id else None
        product.price = request.POST.get('selling_price')
        product.cost_price = request.POST.get('cost_price') or product.cost_price
        product.stock = request.POST.get('stock')
        product.barcode = barcode
        product.description = request.POST.get('description', '').strip() or None
        product.save()
        messages.success(request, "Product updated successfully.")
        return redirect('product_list')

    return render(request, 'supermarket/product_form.html', _product_form_context(
        product=product, categories=categories, suppliers=suppliers,
    ))


@login_required(login_url='login')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        if product.image:
            product.image.delete(save=False)
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect('product_list')
    return render(request, 'supermarket/product_confirm_delete.html', {'product': product})


@login_required(login_url='login')
def customer_list(request):
    search_query = request.GET.get('search', '')
    customers = Customer.objects.all().order_by('-id')
    if search_query:
        customers = customers.filter(
            Q(full_name__icontains=search_query) | Q(phone__icontains=search_query)
        )

    paginator = Paginator(customers, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'supermarket/customer_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'customers': customers,
    })


@login_required(login_url='login')
def customer_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        if name:
            if phone and Customer.objects.filter(phone=phone).exists():
                messages.error(request, "A customer with this phone number already exists.")
                return redirect('customer_list')
            Customer.objects.create(
                full_name=name,
                phone=phone or None,
                email=email or None,
                address=address or None,
            )
            messages.success(request, "Customer saved successfully.")
            return redirect('customer_list')
        messages.error(request, "Please enter a customer name.")
    return redirect('customer_list')


@login_required(login_url='login')
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        if not name:
            messages.error(request, "Please enter a customer name.")
            return render(request, 'supermarket/customer_form.html', {'customer': customer})
        if phone and Customer.objects.filter(phone=phone).exclude(pk=customer.pk).exists():
            messages.error(request, "A customer with this phone number already exists.")
            return render(request, 'supermarket/customer_form.html', {'customer': customer})

        customer.full_name = name
        customer.phone = phone or None
        customer.email = request.POST.get('email', '').strip() or None
        customer.address = request.POST.get('address', '').strip() or None
        customer.save()
        messages.success(request, "Customer updated successfully.")
        return redirect('customer_list')
    return render(request, 'supermarket/customer_form.html', {'customer': customer})


@login_required(login_url='login')
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, "Customer deleted successfully.")
        return redirect('customer_list')
    return render(request, 'supermarket/customer_confirm_delete.html', {'customer': customer})


@login_required(login_url='login')
def order_list(request):
    search_query = request.GET.get('search', '')
    orders = Order.objects.select_related('customer').order_by('-date_ordered')
    if search_query:
        orders = orders.filter(customer__full_name__icontains=search_query)

    paginator = Paginator(orders, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'supermarket/order_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
    })


@login_required(login_url='login')
def order_create(request):
    customers = Customer.objects.all()
    products = Product.objects.filter(stock__gt=0).select_related('category').order_by('name')

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        product_ids = request.POST.getlist('products')

        if not customer_id:
            messages.error(request, 'Please select a customer.')
        elif not product_ids:
            messages.error(request, 'Please select at least one product.')
        else:
            customer = get_object_or_404(Customer, id=customer_id)
            quantities = parse_product_quantities(product_ids, request.POST)
            tax = parse_decimal(request.POST.get('tax'))
            discount = parse_decimal(request.POST.get('discount'))

            try:
                with transaction.atomic():
                    order = Order.objects.create(customer=customer, user=request.user)
                    subtotal = create_order_with_items(order, quantities)
                    order.total_amount = calculate_grand_total(subtotal, tax, discount)
                    order.save(update_fields=['total_amount'])
            except OrderProcessingError as exc:
                messages.error(request, str(exc))
            except Product.DoesNotExist:
                messages.error(request, 'One or more selected products no longer exist.')
            else:
                messages.success(request, f'Order #{order.id} created successfully.')
                return redirect('invoice', pk=order.id)

    return render(request, 'supermarket/order_form.html', {
        'customers': customers,
        'products': products,
    })


@login_required(login_url='login')
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        for item in order.items.select_related('product'):
            item.product.stock += item.quantity
            item.product.save()
        order.delete()
        messages.success(request, "Order deleted. Stock has been restored.")
        return redirect('order_list')
    return render(request, 'supermarket/order_confirm_delete.html', {'order': order})


@login_required(login_url='login')
def invoice(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('customer', 'user').prefetch_related('items__product'),
        pk=pk,
    )
    return render(request, 'supermarket/invoice.html', {'order': order})


@login_required(login_url='login')
def pos_view(request):
    products = Product.objects.filter(stock__gt=0).select_related('category').order_by('name')
    customers = Customer.objects.all().order_by('full_name')

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        product_ids = request.POST.getlist('products')

        if not customer_id:
            messages.error(request, 'Please select a customer before checkout.')
        elif not product_ids:
            messages.error(request, 'Cart is empty. Add at least one product.')
        else:
            customer = get_object_or_404(Customer, id=customer_id)
            quantities = parse_product_quantities(product_ids, request.POST)
            tax = parse_decimal(request.POST.get('tax'))
            discount = parse_decimal(request.POST.get('discount'))

            try:
                with transaction.atomic():
                    order = Order.objects.create(customer=customer, user=request.user)
                    subtotal = create_order_with_items(order, quantities)
                    order.total_amount = calculate_grand_total(subtotal, tax, discount)
                    order.save(update_fields=['total_amount'])
            except OrderProcessingError as exc:
                messages.error(request, str(exc))
            except Product.DoesNotExist:
                messages.error(request, 'One or more products in the cart are no longer available.')
            else:
                messages.success(request, f'Sale completed! Order #{order.id}')
                return redirect('invoice', pk=order.id)

    products_data = [
        {
            'id': p.id,
            'name': p.name,
            'price': float(p.price),
            'stock': p.stock,
            'barcode': p.barcode,
            'sku': extract_sku(p.description),
            'image': p.image.url if p.image else '',
        }
        for p in products
    ]

    return render(request, 'supermarket/pos.html', {
        'products': products,
        'products_data': products_data,
        'customers': customers,
    })


@login_required(login_url='login')
def sales_list(request):
    from django.db.models import Sum

    orders = Order.objects.select_related('customer', 'user').order_by('-date_ordered')
    product_sales = (
        OrderItem.objects
        .values('product__name', 'product__id')
        .annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum('subtotal'),
        )
        .order_by('-quantity_sold')
    )
    return render(request, 'supermarket/sales_list.html', {
        'orders': orders,
        'product_sales': product_sales,
    })
