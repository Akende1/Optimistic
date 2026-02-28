"""
Seed the database with realistic Zambian marketplace data.

Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from apps.products.models import Category, Product
from apps.sellers.models import Seller
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    """
    Seed database with realistic Zambian marketplace data.
    
    Purpose: Populate empty database for development and testing
    
    What it creates:
    - 1 admin user (username: admin, password: admin123)
    - 5 seller users (username: seller1-5, password: seller123)
    - 5 seller profiles (some verified, some unverified for testing)
    - 8 product categories (Electronics, Fashion, Food, etc.)
    - Multiple products with Zambian pricing (ZMW)
    
    Usage:
        python manage.py seed_data
        
    Safe to run multiple times:
    - Uses get_or_create() to prevent duplicates
    - Checks if data exists before creating
    - Idempotent: Same result whether run once or 100 times
    
    Zambian Context:
    - Prices in ZMW (Zambian Kwacha)
    - Realistic product names (local foods, etc.)
    - Local categories
    - Phone numbers in Zambian format
    
    Why Seed Data?
    - Development: Test UI with realistic data
    - Testing: Run automated tests against known dataset
    - Demo: Show functionality to stakeholders
    - QA: Verify workflows work end-to-end
    
    Security Warning:
    - Uses weak passwords (admin123, seller123)
    - ONLY for development/testing environments
    - NEVER run on production
    - Production must use strong passwords + 2FA
    """
    help = 'Seed database with initial data for Optimistic'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting data seed...'))

        # Create admin user
        self.create_admin()

        # Create categories
        categories = self.create_categories()

        # Create sellers (verified and unverified)
        sellers = self.create_sellers()

        # Create products
        self.create_products(categories, sellers)

        self.stdout.write(self.style.SUCCESS('✅ Database seeded successfully!'))

    def create_admin(self):
        """Create admin user if not exists."""
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@zustore.zm',
                password='admin123',
                role='ADMIN'
            )
            self.stdout.write('✓ Admin user created (admin/admin123)')
        else:
            self.stdout.write('✓ Admin user already exists')

    def create_categories(self):
        """Create product categories."""
        category_names = [
            'Electronics',
            'Fashion',
            'Groceries',
            'Home & Furniture',
            'Services',
            'Books & Stationery',
            'Beauty & Health',
            'Sports & Outdoors',
        ]

        categories = []
        for name in category_names:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'slug': slugify(name), 'is_active': True}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'✓ Created category: {name}')

        return categories

    def create_sellers(self):
        """Create test sellers."""
        sellers_data = [
            {'username': 'chanda_electronics', 'store': 'Chanda Electronics', 'phone': '+260971234567', 'verified': True},
            {'username': 'mwamba_fashion', 'store': 'Mwamba Fashion House', 'phone': '+260977654321', 'verified': True},
            {'username': 'zulu_groceries', 'store': 'Zulu Fresh Groceries', 'phone': '+260969876543', 'verified': True},
            {'username': 'tembo_furniture', 'store': 'Tembo Home Furnishings', 'phone': '+260955123456', 'verified': False},
            {'username': 'banda_services', 'store': 'Banda Tech Services', 'phone': '+260966789012', 'verified': False},
        ]

        sellers = []
        for data in sellers_data:
            # Create user
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': f"{data['username']}@zustore.zm",
                    'role': 'SELLER'
                }
            )
            if created:
                user.set_password('seller123')
                user.save()

            # Create seller profile
            seller, created = Seller.objects.get_or_create(
                user=user,
                defaults={
                    'store_name': data['store'],
                    'phone': data['phone'],
                    'verified': data['verified']
                }
            )
            sellers.append(seller)

            status = '✓ VERIFIED' if seller.verified else '⏳ UNVERIFIED'
            self.stdout.write(f'{status} Seller: {data["store"]}')

        return sellers

    def create_products(self, categories, sellers):
        """Create sample products."""
        products_data = [
            # Electronics
            {
                'name': 'Samsung Galaxy A54 5G',
                'category': 'Electronics',
                'price': '3500.00',
                'stock': 15,
                'status': 'ACTIVE',
                'description': 'Latest Samsung smartphone with 5G connectivity, 128GB storage, 50MP camera.',
                'seller': 'Chanda Electronics'
            },
            {
                'name': 'HP Laptop 15s',
                'category': 'Electronics',
                'price': '5200.00',
                'stock': 8,
                'status': 'ACTIVE',
                'description': 'HP 15.6" laptop, Intel Core i5, 8GB RAM, 512GB SSD, Windows 11.',
                'seller': 'Chanda Electronics'
            },
            {
                'name': 'JBL Bluetooth Speaker',
                'category': 'Electronics',
                'price': '450.00',
                'stock': 25,
                'status': 'DRAFT',
                'description': 'Portable wireless speaker, 10-hour battery, waterproof.',
                'seller': 'Chanda Electronics'
            },
            # Fashion
            {
                'name': 'Chitenge Dress',
                'category': 'Fashion',
                'price': '250.00',
                'stock': 30,
                'status': 'ACTIVE',
                'description': 'Beautiful handmade chitenge dress, available in multiple sizes.',
                'seller': 'Mwamba Fashion House'
            },
            {
                'name': 'Men\'s Formal Suit',
                'category': 'Fashion',
                'price': '850.00',
                'stock': 12,
                'status': 'ACTIVE',
                'description': 'Classic black formal suit, tailored fit, jacket and trousers.',
                'seller': 'Mwamba Fashion House'
            },
            {
                'name': 'Leather Handbag',
                'category': 'Fashion',
                'price': '320.00',
                'stock': 18,
                'status': 'ACTIVE',
                'description': 'Genuine leather handbag, spacious with multiple compartments.',
                'seller': 'Mwamba Fashion House'
            },
            # Groceries
            {
                'name': 'Kapenta (Dried Fish) 1kg',
                'category': 'Groceries',
                'price': '85.00',
                'stock': 50,
                'status': 'ACTIVE',
                'description': 'Fresh Kapenta from Lake Tanganyika, 1kg pack.',
                'seller': 'Zulu Fresh Groceries'
            },
            {
                'name': 'Roller Meal 25kg',
                'category': 'Groceries',
                'price': '280.00',
                'stock': 100,
                'status': 'ACTIVE',
                'description': 'High-quality roller meal, 25kg bag.',
                'seller': 'Zulu Fresh Groceries'
            },
            {
                'name': 'Cooking Oil 5L',
                'category': 'Groceries',
                'price': '150.00',
                'stock': 40,
                'status': 'ACTIVE',
                'description': 'Pure vegetable cooking oil, 5 liter bottle.',
                'seller': 'Zulu Fresh Groceries'
            },
            # Home & Furniture
            {
                'name': 'Dining Table Set (6 chairs)',
                'category': 'Home & Furniture',
                'price': '2800.00',
                'stock': 5,
                'status': 'DRAFT',
                'description': 'Wooden dining table with 6 matching chairs, modern design.',
                'seller': 'Tembo Home Furnishings'
            },
            {
                'name': 'Double Bed Frame',
                'category': 'Home & Furniture',
                'price': '1200.00',
                'stock': 10,
                'status': 'DRAFT',
                'description': 'Sturdy wooden double bed frame with headboard.',
                'seller': 'Tembo Home Furnishings'
            },
            # Services
            {
                'name': 'Laptop Repair Service',
                'category': 'Services',
                'price': '200.00',
                'stock': 999,
                'status': 'DRAFT',
                'description': 'Professional laptop repair, diagnosis and service.',
                'seller': 'Banda Tech Services'
            },
        ]

        # Category and seller lookup
        cat_map = {cat.name: cat for cat in categories}
        seller_map = {s.store_name: s for s in sellers}

        for data in products_data:
            category = cat_map.get(data['category'])
            seller = seller_map.get(data['seller'])

            if not category or not seller:
                continue

            product, created = Product.objects.get_or_create(
                name=data['name'],
                seller=seller,
                defaults={
                    'category': category,
                    'description': data['description'],
                    'price': Decimal(data['price']),
                    'stock': data['stock'],
                    'status': data['status']
                }
            )

            if created:
                status_icon = '✓' if data['status'] == 'ACTIVE' else '⏳'
                self.stdout.write(f'{status_icon} Product: {data["name"]} (K{data["price"]})')
