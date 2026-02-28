"""
Management command to seed demo/dummy data for Optimistic
Usage: python manage.py seed_demo_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal
from apps.accounts.models import User
from apps.sellers.models import Seller
from apps.products.models import Category, Product, ProductImage
from apps.orders.models import Order
from apps.reviews.models import Review
from apps.notifications.models import Notification


class Command(BaseCommand):
    help = 'Seeds the database with demo/dummy data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            # Don't delete admin users
            User.objects.filter(is_staff=False).delete()
            Product.objects.all().delete()
            Order.objects.all().delete()
            Review.objects.all().delete()
            Notification.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Data cleared'))

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))

        # Create categories
        self.stdout.write('Creating categories...')
        categories = []
        category_names = [
            'Electronics', 'Fashion', 'Home & Garden', 'Sports', 
            'Books', 'Toys', 'Food & Drinks', 'Beauty'
        ]
        for name in category_names:
            slug = name.lower().replace(' & ', '-').replace(' ', '-')
            cat, created = Category.objects.get_or_create(
                name=name,
                defaults={'slug': slug, 'is_active': True}
            )
            categories.append(cat)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(categories)} categories'))

        # Create buyer users
        self.stdout.write('Creating buyers...')
        buyers = []
        buyer_names = ['john_buyer', 'jane_shopper', 'mike_customer', 'sarah_buyer', 'david_shop']
        for i, username in enumerate(buyer_names, 1):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'role': 'BUYER',
                    'is_active': True
                }
            )
            if created:
                user.set_password('buyer123')
                user.save()
            buyers.append(user)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(buyers)} buyers'))

        # Create seller users
        self.stdout.write('Creating sellers...')
        sellers = []
        seller_data = [
            ('techstore', 'Tech Store ZM', True),
            ('fashionhub', 'Fashion Hub', True),
            ('homegarden', 'Home & Garden Plus', True),
            ('sportsworld', 'Sports World', False),  # Unverified
            ('bookshop', 'Book Shop Zambia', True),
        ]
        
        for username, store_name, is_verified in seller_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'role': 'SELLER',
                    'is_active': True
                }
            )
            if created:
                user.set_password('seller123')
                user.save()
            
            seller, created = Seller.objects.get_or_create(
                user=user,
                defaults={
                    'store_name': store_name,
                    'verified': is_verified,
                    'phone': f'+260{random.randint(900000000, 999999999)}'
                }
            )
            sellers.append(seller)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(sellers)} sellers'))

        # Create products
        self.stdout.write('Creating products...')
        products = []
        product_data = [
            # Electronics
            ('iPhone 13 Pro', 'Electronics', 'techstore', 12500, 15, 'ACTIVE'),
            ('Samsung Galaxy S22', 'Electronics', 'techstore', 10500, 20, 'ACTIVE'),
            ('MacBook Pro M1', 'Electronics', 'techstore', 25000, 8, 'ACTIVE'),
            ('Sony Headphones', 'Electronics', 'techstore', 1500, 30, 'PENDING_APPROVAL'),
            
            # Fashion
            ('Nike Air Max', 'Fashion', 'fashionhub', 850, 50, 'ACTIVE'),
            ('Adidas Tracksuit', 'Fashion', 'fashionhub', 650, 40, 'ACTIVE'),
            ('Denim Jeans', 'Fashion', 'fashionhub', 350, 60, 'ACTIVE'),
            ('Summer Dress', 'Fashion', 'fashionhub', 450, 35, 'ACTIVE'),
            
            # Home & Garden
            ('Sofa Set 5-Seater', 'Home & Garden', 'homegarden', 4500, 5, 'ACTIVE'),
            ('Dining Table', 'Home & Garden', 'homegarden', 3200, 8, 'ACTIVE'),
            ('Garden Tools Kit', 'Home & Garden', 'homegarden', 450, 25, 'ACTIVE'),
            
            # Sports
            ('Football', 'Sports', 'sportsworld', 250, 100, 'PENDING_APPROVAL'),
            ('Basketball', 'Sports', 'sportsworld', 280, 80, 'ACTIVE'),
            ('Tennis Racket', 'Sports', 'sportsworld', 850, 30, 'ACTIVE'),
            
            # Books
            ('Python Programming', 'Books', 'bookshop', 120, 50, 'ACTIVE'),
            ('Business Strategy', 'Books', 'bookshop', 150, 40, 'ACTIVE'),
        ]
        
        for name, cat_name, seller_username, price, stock_qty, status in product_data:
            category = Category.objects.get(name=cat_name)
            seller = Seller.objects.get(user__username=seller_username)
            
            # Random created date within last 30 days
            days_ago = random.randint(0, 30)
            created_at = timezone.now() - timedelta(days=days_ago)
            
            product, created = Product.objects.get_or_create(
                name=name,
                seller=seller,
                defaults={
                    'category': category,
                    'description': f'High-quality {name}. Perfect condition.',
                    'price': Decimal(str(price)),
                    'stock': stock_qty,
                    'status': status,
                    'created_at': created_at,
                }
            )
            if created:
                product.created_at = created_at
                product.save()
            products.append(product)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(products)} products'))

        # Create orders
        self.stdout.write('Creating orders...')
        orders = []
        statuses = ['PENDING', 'PAID', 'READY_FOR_DELIVERY', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED']
        
        for i in range(50):  # Create 50 orders
            buyer = random.choice(buyers)
            status = random.choice(statuses)
            
            # Random date within last 60 days
            days_ago = random.randint(0, 60)
            created_at = timezone.now() - timedelta(days=days_ago)
            
            # Random order total between 50 and 500 ZMW
            total_amount = Decimal(str(random.uniform(50, 500))).quantize(Decimal('0.01'))
            
            order = Order.objects.create(
                buyer=buyer,
                status=status,
                total_amount=total_amount,
                created_at=created_at,
            )
            order.created_at = created_at
            order.save()
            orders.append(order)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(orders)} orders'))

        # Create reviews
        self.stdout.write('Creating reviews...')
        reviews = []
        delivered_orders = Order.objects.filter(status='DELIVERED')
        
        for order in delivered_orders[:20]:  # Review first 20 delivered orders
            # Since we don't have OrderItem, just review a random product
            product = random.choice([p for p in products if p.status == 'ACTIVE'])
            rating = random.randint(3, 5)
            comments = [
                'Great product! Very satisfied.',
                'Good quality, fast delivery.',
                'Excellent service!',
                'As described, would buy again.',
                'Amazing product, highly recommend!',
                'Perfect! Would definitely order again.',
                'Excellent quality and fast shipping.',
            ]
            
            try:
                review, created = Review.objects.get_or_create(
                    order=order,
                    product=product,
                    reviewer=order.buyer,
                    defaults={
                        'seller': product.seller,
                        'rating': rating,
                        'comment': random.choice(comments)
                    }
                )
                if created:
                    reviews.append(review)
            except Exception:
                pass  # Skip if duplicate
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(reviews)} reviews'))

        # Create notifications
        self.stdout.write('Creating notifications...')
        notifications = []
        
        for user in User.objects.all()[:10]:
            notification_types = [
                ('order', 'Your order has been shipped'),
                ('product', 'New product in your wishlist category'),
                ('seller', 'Your seller account has been verified'),
                ('review', 'New review on your product'),
            ]
            
            for ntype, message in random.sample(notification_types, 2):
                notif = Notification.objects.create(
                    user=user,
                    notification_type=ntype,
                    message=message,
                    is_read=random.choice([True, False])
                )
                notifications.append(notif)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(notifications)} notifications'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('✅ SEEDING COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'📊 Categories: {Category.objects.count()}')
        self.stdout.write(f'👥 Users: {User.objects.count()} (Buyers: {User.objects.filter(role="BUYER").count()}, Sellers: {User.objects.filter(role="SELLER").count()})')
        self.stdout.write(f'🏪 Sellers: {Seller.objects.count()} (Verified: {Seller.objects.filter(verified=True).count()})')
        self.stdout.write(f'📦 Products: {Product.objects.count()} (Active: {Product.objects.filter(status="ACTIVE").count()}, Pending: {Product.objects.filter(status="PENDING_APPROVAL").count()})')
        self.stdout.write(f'🛒 Orders: {Order.objects.count()}')
        self.stdout.write(f'⭐ Reviews: {Review.objects.count()}')
        self.stdout.write(f'🔔 Notifications: {Notification.objects.count()}')
        self.stdout.write(self.style.SUCCESS('='*50))
        
        self.stdout.write(self.style.WARNING('\n📝 Test Credentials:'))
        self.stdout.write('  Buyer: john_buyer / buyer123')
        self.stdout.write('  Seller: techstore / seller123')
        self.stdout.write('  Admin: Admin / 1234')
