import shutil
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from supermarket.models import Category, Product

CATEGORIES = [
    {'name': 'Beverages', 'description': 'Soft drinks, juices, and bottled water.'},
    {'name': 'Groceries', 'description': 'Staple food items and cooking essentials.'},
    {'name': 'Snacks', 'description': 'Chips, biscuits, cookies, and quick bites.'},
    {'name': 'Household Items', 'description': 'Cleaning supplies and home essentials.'},
    {'name': 'Personal Care', 'description': 'Hygiene and personal grooming products.'},
]

PRODUCTS = [
    # Beverages
    {
        'name': 'Coca-Cola 330ml',
        'category': 'Beverages',
        'sku': 'BEV-001',
        'barcode': '8901001001001',
        'cost_price': Decimal('0.65'),
        'price': Decimal('1.25'),
        'stock': 120,
        'reorder_level': 24,
        'description': 'Classic cola soft drink in a 330ml can.',
    },
    {
        'name': 'Pepsi 330ml',
        'category': 'Beverages',
        'sku': 'BEV-002',
        'barcode': '8901001001002',
        'cost_price': Decimal('0.63'),
        'price': Decimal('1.20'),
        'stock': 110,
        'reorder_level': 24,
        'description': 'Refreshing cola beverage in a 330ml can.',
    },
    {
        'name': 'Sprite 330ml',
        'category': 'Beverages',
        'sku': 'BEV-003',
        'barcode': '8901001001003',
        'cost_price': Decimal('0.62'),
        'price': Decimal('1.20'),
        'stock': 95,
        'reorder_level': 20,
        'description': 'Lemon-lime carbonated soft drink, 330ml can.',
    },
    {
        'name': 'Fanta Orange 330ml',
        'category': 'Beverages',
        'sku': 'BEV-004',
        'barcode': '8901001001004',
        'cost_price': Decimal('0.60'),
        'price': Decimal('1.15'),
        'stock': 88,
        'reorder_level': 20,
        'description': 'Orange-flavored fizzy drink in a 330ml can.',
    },
    {
        'name': 'Mineral Water 500ml',
        'category': 'Beverages',
        'sku': 'BEV-005',
        'barcode': '8901001001005',
        'cost_price': Decimal('0.35'),
        'price': Decimal('0.75'),
        'stock': 200,
        'reorder_level': 40,
        'description': 'Purified still mineral water, 500ml bottle.',
    },
    # Groceries
    {
        'name': 'Rice 25kg',
        'category': 'Groceries',
        'sku': 'GRO-001',
        'barcode': '8902002002001',
        'cost_price': Decimal('18.50'),
        'price': Decimal('24.99'),
        'stock': 45,
        'reorder_level': 10,
        'description': 'Long-grain white rice sack, 25kg.',
    },
    {
        'name': 'Sugar 1kg',
        'category': 'Groceries',
        'sku': 'GRO-002',
        'barcode': '8902002002002',
        'cost_price': Decimal('0.85'),
        'price': Decimal('1.49'),
        'stock': 150,
        'reorder_level': 30,
        'description': 'Refined white sugar pack, 1kg.',
    },
    {
        'name': 'Wheat Flour 10kg',
        'category': 'Groceries',
        'sku': 'GRO-003',
        'barcode': '8902002002003',
        'cost_price': Decimal('6.20'),
        'price': Decimal('8.75'),
        'stock': 60,
        'reorder_level': 12,
        'description': 'All-purpose wheat flour bag, 10kg.',
    },
    {
        'name': 'Cooking Oil 3L',
        'category': 'Groceries',
        'sku': 'GRO-004',
        'barcode': '8902002002004',
        'cost_price': Decimal('7.80'),
        'price': Decimal('10.99'),
        'stock': 55,
        'reorder_level': 12,
        'description': 'Sunflower cooking oil bottle, 3 liters.',
    },
    {
        'name': 'Pasta 500g',
        'category': 'Groceries',
        'sku': 'GRO-005',
        'barcode': '8902002002005',
        'cost_price': Decimal('0.95'),
        'price': Decimal('1.69'),
        'stock': 130,
        'reorder_level': 25,
        'description': 'Durum wheat spaghetti pack, 500g.',
    },
    # Snacks
    {
        'name': 'Potato Chips',
        'category': 'Snacks',
        'sku': 'SNK-001',
        'barcode': '8903003003001',
        'cost_price': Decimal('1.10'),
        'price': Decimal('1.99'),
        'stock': 90,
        'reorder_level': 18,
        'description': 'Crispy salted potato chips, 150g bag.',
    },
    {
        'name': 'Chocolate Cookies',
        'category': 'Snacks',
        'sku': 'SNK-002',
        'barcode': '8903003003002',
        'cost_price': Decimal('1.40'),
        'price': Decimal('2.49'),
        'stock': 75,
        'reorder_level': 15,
        'description': 'Chocolate chip cookies pack, 200g.',
    },
    {
        'name': 'Salted Biscuits',
        'category': 'Snacks',
        'sku': 'SNK-003',
        'barcode': '8903003003003',
        'cost_price': Decimal('0.90'),
        'price': Decimal('1.59'),
        'stock': 100,
        'reorder_level': 20,
        'description': 'Classic salted crackers, 250g pack.',
    },
    {
        'name': 'Popcorn',
        'category': 'Snacks',
        'sku': 'SNK-004',
        'barcode': '8903003003004',
        'cost_price': Decimal('0.75'),
        'price': Decimal('1.35'),
        'stock': 85,
        'reorder_level': 17,
        'description': 'Microwave butter popcorn, 3-pack.',
    },
    {
        'name': 'Mixed Nuts',
        'category': 'Snacks',
        'sku': 'SNK-005',
        'barcode': '8903003003005',
        'cost_price': Decimal('3.20'),
        'price': Decimal('4.99'),
        'stock': 50,
        'reorder_level': 10,
        'description': 'Roasted mixed nuts assortment, 300g.',
    },
    # Household Items
    {
        'name': 'Laundry Detergent',
        'category': 'Household Items',
        'sku': 'HOU-001',
        'barcode': '8904004004001',
        'cost_price': Decimal('5.50'),
        'price': Decimal('8.49'),
        'stock': 40,
        'reorder_level': 8,
        'description': 'Concentrated laundry detergent, 2L bottle.',
    },
    {
        'name': 'Dishwashing Liquid',
        'category': 'Household Items',
        'sku': 'HOU-002',
        'barcode': '8904004004002',
        'cost_price': Decimal('1.80'),
        'price': Decimal('2.99'),
        'stock': 70,
        'reorder_level': 14,
        'description': 'Lemon-scented dishwashing liquid, 750ml.',
    },
    {
        'name': 'Toilet Paper',
        'category': 'Household Items',
        'sku': 'HOU-003',
        'barcode': '8904004004003',
        'cost_price': Decimal('4.20'),
        'price': Decimal('6.49'),
        'stock': 65,
        'reorder_level': 12,
        'description': 'Soft 2-ply toilet tissue, 12-roll pack.',
    },
    {
        'name': 'Trash Bags',
        'category': 'Household Items',
        'sku': 'HOU-004',
        'barcode': '8904004004004',
        'cost_price': Decimal('2.10'),
        'price': Decimal('3.49'),
        'stock': 80,
        'reorder_level': 16,
        'description': 'Heavy-duty kitchen trash bags, 30 count.',
    },
    {
        'name': 'Multi-Purpose Cleaner',
        'category': 'Household Items',
        'sku': 'HOU-005',
        'barcode': '8904004004005',
        'cost_price': Decimal('2.40'),
        'price': Decimal('3.99'),
        'stock': 58,
        'reorder_level': 12,
        'description': 'All-surface spray cleaner, 1L bottle.',
    },
    # Personal Care
    {
        'name': 'Shampoo',
        'category': 'Personal Care',
        'sku': 'PER-001',
        'barcode': '8905005005001',
        'cost_price': Decimal('3.10'),
        'price': Decimal('4.99'),
        'stock': 72,
        'reorder_level': 14,
        'description': 'Daily care shampoo for all hair types, 400ml.',
    },
    {
        'name': 'Toothpaste',
        'category': 'Personal Care',
        'sku': 'PER-002',
        'barcode': '8905005005002',
        'cost_price': Decimal('1.60'),
        'price': Decimal('2.79'),
        'stock': 140,
        'reorder_level': 28,
        'description': 'Fluoride toothpaste with mint freshness, 100ml.',
    },
    {
        'name': 'Bath Soap',
        'category': 'Personal Care',
        'sku': 'PER-003',
        'barcode': '8905005005003',
        'cost_price': Decimal('0.70'),
        'price': Decimal('1.25'),
        'stock': 160,
        'reorder_level': 32,
        'description': 'Moisturizing bath soap bar, 125g.',
    },
    {
        'name': 'Body Lotion',
        'category': 'Personal Care',
        'sku': 'PER-004',
        'barcode': '8905005005004',
        'cost_price': Decimal('4.00'),
        'price': Decimal('6.49'),
        'stock': 48,
        'reorder_level': 10,
        'description': 'Hydrating body lotion with aloe vera, 500ml.',
    },
    {
        'name': 'Toothbrush',
        'category': 'Personal Care',
        'sku': 'PER-005',
        'barcode': '8905005005005',
        'cost_price': Decimal('1.20'),
        'price': Decimal('2.19'),
        'stock': 125,
        'reorder_level': 25,
        'description': 'Soft-bristle adult toothbrush with ergonomic grip.',
    },
]


class Command(BaseCommand):
    help = 'Populate the database with sample categories and products for testing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assign-images',
            action='store_true',
            help='Assign placeholder images to products that do not have one.',
        )

    def handle(self, *args, **options):
        categories_created = 0
        categories_skipped = 0
        products_created = 0
        products_skipped = 0
        images_assigned = 0

        category_map = {}
        for item in CATEGORIES:
            category, created = Category.objects.get_or_create(
                name=item['name'],
                defaults={'description': item['description']},
            )
            category_map[item['name']] = category
            if created:
                categories_created += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                categories_skipped += 1
                self.stdout.write(f'Skipped existing category: {category.name}')

        placeholder_path = Path(settings.BASE_DIR) / 'static' / 'img' / 'product-placeholder.svg'

        for item in PRODUCTS:
            category = category_map[item['category']]
            full_description = (
                f"{item['description']} "
                f"SKU: {item['sku']}. Reorder level: {item['reorder_level']}. Status: Active."
            )

            product, created = Product.objects.get_or_create(
                barcode=item['barcode'],
                defaults={
                    'name': item['name'],
                    'category': category,
                    'cost_price': item['cost_price'],
                    'price': item['price'],
                    'stock': item['stock'],
                    'description': full_description,
                },
            )

            if created:
                products_created += 1
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))
            else:
                products_skipped += 1
                self.stdout.write(f'Skipped existing product (barcode {item["barcode"]}): {product.name}')

            if options['assign_images'] and not product.image and placeholder_path.exists():
                media_dir = Path(settings.MEDIA_ROOT) / 'products'
                media_dir.mkdir(parents=True, exist_ok=True)
                target_name = f'{item["sku"].lower()}-placeholder.svg'
                target_path = media_dir / target_name
                if not target_path.exists():
                    shutil.copy(placeholder_path, target_path)
                with target_path.open('rb') as image_file:
                    product.image.save(target_name, File(image_file), save=True)
                images_assigned += 1

        total_categories = Category.objects.count()
        total_products = Product.objects.count()
        products_with_category = Product.objects.filter(category__isnull=False).count()
        target_category_names = {c['name'] for c in CATEGORIES}
        seeded_categories = Category.objects.filter(name__in=target_category_names).count()
        seeded_products = Product.objects.filter(barcode__in=[p['barcode'] for p in PRODUCTS]).count()

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Seed Summary'))
        self.stdout.write(f'Categories created: {categories_created}')
        self.stdout.write(f'Categories skipped: {categories_skipped}')
        self.stdout.write(f'Products created: {products_created}')
        self.stdout.write(f'Products skipped: {products_skipped}')
        self.stdout.write(f'Placeholder images assigned: {images_assigned}')
        self.stdout.write(f'Total categories in database: {total_categories}')
        self.stdout.write(f'Total products in database: {total_products}')
        self.stdout.write(f'Seeded categories present: {seeded_categories}/5')
        self.stdout.write(f'Seeded products present: {seeded_products}/25')
        self.stdout.write(f'Products linked to categories: {products_with_category}/{total_products}')

        if seeded_categories == 5 and seeded_products == 25:
            self.stdout.write(self.style.SUCCESS('Sample data verification passed.'))
        else:
            self.stdout.write(self.style.WARNING('Sample data verification incomplete.'))
