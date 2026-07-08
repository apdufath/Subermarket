from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from PIL import Image

from supermarket.models import Category, Supplier, Product, Customer, Order, OrderItem


class EndToEndAuditTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST='127.0.0.1')
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_all_navigation_pages_load(self):
        urls = [
            reverse('dashboard'),
            reverse('pos'),
            reverse('sales_list'),
            reverse('category_list'),
            reverse('category_create'),
            reverse('supplier_list'),
            reverse('supplier_create'),
            reverse('product_list'),
            reverse('product_create'),
            reverse('customer_list'),
            reverse('order_list'),
            reverse('order_create'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, msg=f'Failed for {url}')

    def test_login_required_redirect(self):
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_logout_ends_session_and_redirects_to_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_logout_link_uses_post_form(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'action="/logout/"')
        self.assertContains(response, 'method="post"')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertNotContains(response, 'href="/logout/"')

    def test_dashboard_counts_match_database(self):
        Category.objects.create(name='Cat A')
        Supplier.objects.create(
            company_name='Sup A', contact_person='John',
            phone='111', email='a@test.com', address='Addr',
        )
        cat = Category.objects.get(name='Cat A')
        Product.objects.create(
            name='Prod A', category=cat, price=Decimal('10.00'),
            cost_price=Decimal('5.00'), stock=5, barcode='BC001',
        )
        Customer.objects.create(full_name='Cust A', phone='222')
        cust = Customer.objects.get(full_name='Cust A')
        Order.objects.create(customer=cust, user=self.user, total_amount=Decimal('10.00'))

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_categories'], Category.objects.count())
        self.assertEqual(response.context['total_products'], Product.objects.count())
        self.assertEqual(response.context['total_suppliers'], Supplier.objects.count())
        self.assertEqual(response.context['total_customers'], Customer.objects.count())
        self.assertEqual(response.context['total_orders'], Order.objects.count())

    def test_category_crud(self):
        response = self.client.post(reverse('category_create'), {
            'name': 'Beverages',
            'description': 'Drinks',
        })
        self.assertEqual(response.status_code, 302)
        category = Category.objects.get(name='Beverages')
        self.assertEqual(category.description, 'Drinks')

        response = self.client.post(reverse('category_update', args=[category.pk]), {
            'name': 'Beverages Updated',
            'description': 'Updated',
        })
        self.assertEqual(response.status_code, 302)
        category.refresh_from_db()
        self.assertEqual(category.name, 'Beverages Updated')

        response = self.client.post(reverse('category_delete', args=[category.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_supplier_crud_and_validation(self):
        response = self.client.post(reverse('supplier_create'), {
            'name': 'Wholesale Co',
            'phone': '555-1111',
            'email': '',
            'address': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Supplier.objects.count(), 0)

        response = self.client.post(reverse('supplier_create'), {
            'name': 'Wholesale Co',
            'phone': '555-1111',
            'email': 'wholesale@test.com',
            'address': '123 Main St',
        })
        self.assertEqual(response.status_code, 302)
        supplier = Supplier.objects.get(company_name='Wholesale Co')

        response = self.client.post(reverse('supplier_update', args=[supplier.pk]), {
            'name': 'Wholesale Co Updated',
            'phone': '555-2222',
            'email': 'updated@test.com',
            'address': '456 Oak Ave',
        })
        self.assertEqual(response.status_code, 302)
        supplier.refresh_from_db()
        self.assertEqual(supplier.company_name, 'Wholesale Co Updated')

        response = self.client.post(reverse('supplier_delete', args=[supplier.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Supplier.objects.filter(pk=supplier.pk).exists())

    def test_product_crud_auto_barcode(self):
        category = Category.objects.create(name='Groceries')
        response = self.client.post(reverse('product_create'), {
            'name': 'Milk',
            'category': category.pk,
            'selling_price': '3.50',
            'cost_price': '2.00',
            'stock': '100',
            'barcode': '',
        })
        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(name='Milk')
        self.assertTrue(product.barcode.startswith('AUTO-'))

        response = self.client.post(reverse('product_update', args=[product.pk]), {
            'name': 'Milk 2L',
            'category': category.pk,
            'selling_price': '4.00',
            'cost_price': '2.50',
            'stock': '90',
            'barcode': product.barcode,
        })
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.name, 'Milk 2L')
        self.assertEqual(product.stock, 90)

        response = self.client.post(reverse('product_delete', args=[product.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_customer_crud(self):
        response = self.client.post(reverse('customer_create'), {
            'name': 'Jane Doe',
            'phone': '',
            'email': 'jane@test.com',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Customer.objects.filter(full_name='Jane Doe').count(), 1)

        customer = Customer.objects.get(full_name='Jane Doe')
        response = self.client.post(reverse('customer_update', args=[customer.pk]), {
            'name': 'Jane Smith',
            'phone': '555-3333',
            'email': 'jane@test.com',
            'address': '789 Pine Rd',
        })
        self.assertEqual(response.status_code, 302)
        customer.refresh_from_db()
        self.assertEqual(customer.full_name, 'Jane Smith')

        response = self.client.post(reverse('customer_delete', args=[customer.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Customer.objects.filter(pk=customer.pk).exists())

    def test_order_crud_stock_and_quantity_mapping(self):
        category = Category.objects.create(name='Snacks')
        product_a = Product.objects.create(
            name='Chips', category=category, price=Decimal('2.00'),
            cost_price=Decimal('1.00'), stock=10, barcode='CH001',
        )
        product_b = Product.objects.create(
            name='Cookies', category=category, price=Decimal('3.00'),
            cost_price=Decimal('1.50'), stock=10, barcode='CK001',
        )
        customer = Customer.objects.create(full_name='Buyer', phone='555-4444')

        response = self.client.post(reverse('order_create'), {
            'customer': customer.pk,
            'products': [str(product_b.pk)],
            f'quantity_{product_a.pk}': '5',
            f'quantity_{product_b.pk}': '3',
        })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(customer=customer)
        items = {item.product_id: item.quantity for item in order.items.all()}
        self.assertEqual(items, {product_b.pk: 3})
        self.assertEqual(order.total_amount, Decimal('9.00'))

        product_a.refresh_from_db()
        product_b.refresh_from_db()
        self.assertEqual(product_a.stock, 10)
        self.assertEqual(product_b.stock, 7)

        response = self.client.get(reverse('invoice', args=[order.pk]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('order_delete', args=[order.pk]))
        self.assertEqual(response.status_code, 302)
        product_b.refresh_from_db()
        self.assertEqual(product_b.stock, 10)
        self.assertFalse(Order.objects.filter(pk=order.pk).exists())

    def test_order_insufficient_stock_rolls_back(self):
        category = Category.objects.create(name='Limited')
        product = Product.objects.create(
            name='Rare Item', category=category, price=Decimal('50.00'),
            cost_price=Decimal('25.00'), stock=2, barcode='RARE01',
        )
        customer = Customer.objects.create(full_name='Shopper', phone='555-5555')

        response = self.client.post(reverse('order_create'), {
            'customer': customer.pk,
            'products': [str(product.pk)],
            f'quantity_{product.pk}': '5',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        product.refresh_from_db()
        self.assertEqual(product.stock, 2)

    def test_category_validation_error(self):
        response = self.client.post(reverse('category_create'), {'name': '', 'description': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.count(), 0)

    def test_admin_accessible(self):
        admin = User.objects.create_superuser('admin2', 'admin2@test.com', 'adminpass')
        self.client.login(username='admin2', password='adminpass')
        response = self.client.get('/admin/')
        self.assertIn(response.status_code, [200, 302])


@override_settings(MEDIA_ROOT=settings.BASE_DIR / 'test_media')
class ProductImageTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST='127.0.0.1')
        self.user = User.objects.create_user(username='imguser', password='testpass123')
        self.client.login(username='imguser', password='testpass123')
        self.category = Category.objects.create(name='Image Cat')

    def _png_file(self, name='test.png'):
        buffer = BytesIO()
        Image.new('RGB', (32, 32), color='red').save(buffer, format='PNG')
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.read(), content_type='image/png')

    def test_upload_and_display_product_image(self):
        response = self.client.post(reverse('product_create'), {
            'name': 'Image Product',
            'category': self.category.pk,
            'selling_price': '5.00',
            'cost_price': '3.00',
            'stock': '10',
            'barcode': 'IMG001',
            'image': self._png_file(),
        })
        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(barcode='IMG001')
        self.assertTrue(product.image)
        self.assertTrue(product.image.name.startswith('products/'))

        response = self.client.get(reverse('product_list'))
        self.assertContains(response, product.image.url)

        response = self.client.get(reverse('product_detail', args=[product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.image.url)

    def test_product_without_image_shows_placeholder(self):
        product = Product.objects.create(
            name='No Image Product',
            category=self.category,
            price=Decimal('4.00'),
            cost_price=Decimal('2.00'),
            stock=5,
            barcode='NOIMG01',
        )
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'product-placeholder.svg')

        response = self.client.get(reverse('product_detail', args=[product.pk]))
        self.assertContains(response, 'product-placeholder.svg')

    def test_invalid_image_rejected(self):
        bad_file = SimpleUploadedFile('bad.txt', b'not an image', content_type='text/plain')
        before = Product.objects.count()
        response = self.client.post(reverse('product_create'), {
            'name': 'Bad Image Product',
            'category': self.category.pk,
            'selling_price': '5.00',
            'cost_price': '3.00',
            'stock': '10',
            'barcode': 'BADIMG01',
            'image': bad_file,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), before)
        self.assertFalse(Product.objects.filter(barcode='BADIMG01').exists())

    def test_replace_and_remove_product_image(self):
        product = Product.objects.create(
            name='Replace Me',
            category=self.category,
            price=Decimal('6.00'),
            cost_price=Decimal('3.00'),
            stock=8,
            barcode='REPL01',
        )
        response = self.client.post(reverse('product_update', args=[product.pk]), {
            'name': 'Replace Me',
            'category': self.category.pk,
            'selling_price': '6.00',
            'cost_price': '3.00',
            'stock': '8',
            'barcode': 'REPL01',
            'image': self._png_file('first.png'),
        })
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertTrue(product.image)
        first_image = product.image.name

        response = self.client.post(reverse('product_update', args=[product.pk]), {
            'name': 'Replace Me',
            'category': self.category.pk,
            'selling_price': '6.00',
            'cost_price': '3.00',
            'stock': '8',
            'barcode': 'REPL01',
            'remove_image': 'on',
        })
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertFalse(product.image)

        response = self.client.post(reverse('product_update', args=[product.pk]), {
            'name': 'Replace Me',
            'category': self.category.pk,
            'selling_price': '6.00',
            'cost_price': '3.00',
            'stock': '8',
            'barcode': 'REPL01',
            'image': self._png_file('second.png'),
        })
        product.refresh_from_db()
        self.assertTrue(product.image)
        self.assertNotEqual(product.image.name, first_image)

    def test_delete_product_removes_image(self):
        product = Product.objects.create(
            name='Delete Image Product',
            category=self.category,
            price=Decimal('7.00'),
            cost_price=Decimal('4.00'),
            stock=3,
            barcode='DELIMG01',
        )
        self.client.post(reverse('product_update', args=[product.pk]), {
            'name': product.name,
            'category': self.category.pk,
            'selling_price': '7.00',
            'cost_price': '4.00',
            'stock': '3',
            'barcode': 'DELIMG01',
            'image': self._png_file(),
        })
        product.refresh_from_db()
        self.assertTrue(product.image)
        image_path = product.image.path

        response = self.client.post(reverse('product_delete', args=[product.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())
        import pathlib
        self.assertFalse(pathlib.Path(image_path).exists())


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST='127.0.0.1')

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome Back')
        self.assertContains(response, 'Sign In')
        self.assertContains(response, reverse('signup'))

    def test_signup_page_renders(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')
        self.assertContains(response, reverse('login'))

    def test_login_works(self):
        User.objects.create_user(username='staff1', password='SecurePass123!')
        response = self.client.post(reverse('login'), {
            'username': 'staff1',
            'password': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_login_invalid_credentials(self):
        User.objects.create_user(username='staff1', password='SecurePass123!')
        response = self.client.post(reverse('login'), {
            'username': 'staff1',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse('signup'), {
            'full_name': 'Jane Doe',
            'username': 'janedoe',
            'email': 'jane@example.com',
            'phone': '555-0100',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))
        self.assertTrue(User.objects.filter(username='janedoe').exists())
        user = User.objects.get(username='janedoe')
        self.assertEqual(user.email, 'jane@example.com')
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Doe')
        self.assertTrue(user.check_password('SecurePass123!'))
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.phone, '555-0100')

    def test_signup_validates_unique_username(self):
        User.objects.create_user(username='taken', password='SecurePass123!')
        response = self.client.post(reverse('signup'), {
            'full_name': 'New User',
            'username': 'taken',
            'email': 'new@example.com',
            'phone': '555-0200',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already taken')

    def test_signup_validates_password_confirmation(self):
        response = self.client.post(reverse('signup'), {
            'full_name': 'New User',
            'username': 'newuser',
            'email': 'new@example.com',
            'phone': '555-0300',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'do not match')
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_signup_redirects_authenticated_user(self):
        User.objects.create_user(username='existing', password='SecurePass123!')
        self.client.login(username='existing', password='SecurePass123!')
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))


class OrderQuantityTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST='127.0.0.1')
        self.user = User.objects.create_user(username='cashier', password='testpass123')
        self.client.login(username='cashier', password='testpass123')
        self.category = Category.objects.create(name='Personal Care')
        self.product = Product.objects.create(
            name='Toothpaste',
            category=self.category,
            price=Decimal('2.00'),
            cost_price=Decimal('1.00'),
            stock=50,
            barcode='TOOTH01',
            description='SKU: PER-002. Reorder level: 10. Status: Active.',
        )
        self.customer = Customer.objects.create(full_name='Walk-in Customer', phone='555-9000')

    def _create_order(self, qty):
        return self.client.post(reverse('order_create'), {
            'customer': self.customer.pk,
            'products': [str(self.product.pk)],
            f'quantity_{self.product.pk}': str(qty),
        })

    def test_quantity_one(self):
        response = self._create_order(1)
        self.assertEqual(response.status_code, 302)
        item = OrderItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.subtotal, Decimal('2.00'))

    def test_quantity_five(self):
        response = self._create_order(5)
        self.assertEqual(response.status_code, 302)
        item = OrderItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.subtotal, Decimal('10.00'))

    def test_quantity_ten(self):
        response = self._create_order(10)
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(customer=self.customer)
        self.assertEqual(order.total_amount, Decimal('20.00'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 40)

    def test_quantity_equals_stock(self):
        response = self._create_order(50)
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)

    def test_quantity_exceeds_stock(self):
        response = self._create_order(51)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Insufficient stock available')
        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 50)

    def test_order_item_stores_subtotal(self):
        self._create_order(10)
        item = OrderItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.price, Decimal('2.00'))
        self.assertEqual(item.subtotal, Decimal('20.00'))

    def test_invoice_shows_quantity_format(self):
        self._create_order(10)
        order = Order.objects.get(customer=self.customer)
        response = self.client.get(reverse('invoice', args=[order.pk]))
        self.assertContains(response, 'Toothpaste')
        self.assertContains(response, '× 10')

    def test_pos_checkout_with_quantity(self):
        response = self.client.post(reverse('pos'), {
            'customer': self.customer.pk,
            'products': [str(self.product.pk)],
            f'quantity_{self.product.pk}': '7',
        })
        self.assertEqual(response.status_code, 302)
        item = OrderItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 7)
        self.assertEqual(item.subtotal, Decimal('14.00'))

    def test_sales_report_shows_quantity_sold(self):
        self._create_order(10)
        response = self.client.get(reverse('sales_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Toothpaste')
        self.assertContains(response, '10')
        self.assertContains(response, '20.00')

    def test_grand_total_with_tax_and_discount(self):
        response = self.client.post(reverse('order_create'), {
            'customer': self.customer.pk,
            'products': [str(self.product.pk)],
            f'quantity_{self.product.pk}': '10',
            'tax': '2.00',
            'discount': '5.00',
        })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(customer=self.customer)
        self.assertEqual(order.total_amount, Decimal('17.00'))
