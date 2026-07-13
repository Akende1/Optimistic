"""
Management command to seed demo/dummy data for Optimistic
Usage: python manage.py seed_demo_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal
from apps.accounts.models import User, BuyerAddress
from apps.sellers.models import Seller
from apps.products.models import Category, Product, ProductImage
from apps.orders.models import Order, OrderItem, OrderFulfillment
from apps.logistics.models import ZambianLocation
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
        parser.add_argument('--buyers', type=int, default=30, help='Target number of demo buyers.')
        parser.add_argument('--sellers', type=int, default=15, help='Target number of demo sellers.')
        parser.add_argument('--products', type=int, default=150, help='Target number of demo products.')
        parser.add_argument('--orders', type=int, default=300, help='Target number of demo orders.')
        parser.add_argument('--seed', type=int, default=260, help='Deterministic random seed.')

    def handle(self, *args, **options):
        random.seed(options['seed'])
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            # Don't delete admin users
            Review.objects.all().delete()
            Notification.objects.all().delete()
            OrderFulfillment.objects.all().delete()
            OrderItem.all_objects.all().delete()
            Order.objects.all().delete()
            Product.objects.all().delete()
            User.objects.filter(is_staff=False).delete()
            self.stdout.write(self.style.SUCCESS('Data cleared'))

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
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} categories'))

        # Create buyer users
        self.stdout.write('Creating buyers...')
        buyers = []
        buyer_names = ['john_buyer', 'jane_shopper', 'mike_customer', 'sarah_buyer', 'david_shop']
        for i, username in enumerate(buyer_names, 1):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'phone_number': f'+26097000{i:04d}',
                    'role': 'BUYER',
                    'is_active': True,
                    'phone_verified': True,
                    'email_verified': True,
                }
            )
            if created:
                user.set_password('buyer123')
            user.phone_verified = True
            user.email_verified = True
            user.save()
            buyers.append(user)
        self.stdout.write(self.style.SUCCESS(f'Created {len(buyers)} buyers'))

        for i in range(len(buyers) + 1, max(options['buyers'], len(buyers)) + 1):
            username = f'demo_buyer_{i:03d}'
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': f'{username}@example.com', 'phone_number': f'+260950{i:06d}',
                'role': 'BUYER', 'is_active': True, 'phone_verified': True, 'email_verified': True,
            })
            if created:
                user.set_password('buyer123')
                user.save()
            buyers.append(user)

        zones = list(ZambianLocation.objects.filter(location_type='ZONE'))
        if zones:
            for index, buyer in enumerate(buyers):
                zone = zones[index % len(zones)]
                BuyerAddress.objects.get_or_create(user=buyer, label='Home', defaults={
                    'street_address': f'Plot {100 + index}, Demo Road', 'location': zone,
                    'town_city': zone.parent.name if zone.parent else zone.name,
                    'province': zone.get_full_address(), 'delivery_notes': 'Call on arrival', 'is_default': True,
                })

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
        
        for seller_index, (username, store_name, is_verified) in enumerate(seller_data, 1):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'phone_number': f'+26096000{seller_index:04d}',
                    'role': 'SELLER',
                    'is_active': True,
                    'phone_verified': True,
                    'email_verified': True,
                }
            )
            if created:
                user.set_password('seller123')
            user.phone_verified = True
            user.email_verified = True
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
        self.stdout.write(self.style.SUCCESS(f'Created {len(sellers)} sellers'))

        for i in range(len(sellers) + 1, max(options['sellers'], len(sellers)) + 1):
            username = f'demo_seller_{i:03d}'
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': f'{username}@example.com', 'phone_number': f'+260940{i:06d}',
                'role': 'SELLER', 'is_active': True, 'phone_verified': True, 'email_verified': True,
            })
            if created:
                user.set_password('seller123')
                user.save()
            seller, _ = Seller.objects.get_or_create(user=user, defaults={
                'store_name': f'Demo Marketplace Store {i}', 'verified': True,
                'verification_status': 'VERIFIED', 'phone': user.phone_number,
            })
            sellers.append(seller)

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
        self.stdout.write(self.style.SUCCESS(f'Created {len(products)} products'))

        product_words = ['Premium', 'Classic', 'Smart', 'Everyday', 'Professional', 'Eco', 'Compact', 'Deluxe']
        while Product.objects.count() < options['products']:
            index = Product.objects.count() + 1
            category = categories[index % len(categories)]
            seller = sellers[index % len(sellers)]
            name = f'{random.choice(product_words)} {category.name} Item {index:03d}'
            product, _ = Product.objects.get_or_create(name=name, seller=seller, defaults={
                'category': category, 'description': f'Demo {category.name.lower()} product for mobile and web testing.',
                'price': Decimal(random.randrange(50, 25000)), 'stock': random.randrange(0, 101),
                'status': random.choices(['ACTIVE', 'DRAFT', 'PENDING_APPROVAL'], weights=[8, 1, 1])[0],
            })
            products.append(product)
        products = list(Product.objects.all())

        # Create orders
        self.stdout.write('Creating orders...')
        orders = []
        statuses = ['PENDING', 'PAID', 'READY_FOR_DELIVERY', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED']
        
        orders_to_create = max(options['orders'] - Order.objects.count(), 0)
        for i in range(orders_to_create):
            buyer = random.choice(buyers)
            status = random.choice(statuses)
            
            # Random date within last 60 days
            days_ago = random.randint(0, 60)
            created_at = timezone.now() - timedelta(days=days_ago)
            
            order = Order.objects.create(
                buyer=buyer,
                status=status,
                total_amount=Decimal('0.00'),
                product_subtotal=Decimal('0.00'),
                shipping_address=f'Plot {random.randrange(1, 999)}, Demo Road, Zambia',
                created_at=created_at,
            )
            selected_products = random.sample([p for p in products if p.status == 'ACTIVE'], k=random.randrange(1, 4))
            subtotal = Decimal('0.00')
            seller_ids = set()
            for product in selected_products:
                quantity = random.randrange(1, 4)
                OrderItem.objects.create(order=order, product=product, seller=product.seller,
                                         quantity=quantity, price_snapshot=product.price)
                subtotal += product.price * quantity
                seller_ids.add(product.seller_id)
            order.product_subtotal = subtotal
            order.total_amount = subtotal
            order.created_at = created_at
            order.save(update_fields=['product_subtotal', 'total_amount', 'created_at'])
            fulfillment_status = {
                'PENDING': 'AWAITING_ACCEPTANCE', 'PAID': 'ACCEPTED',
                'READY_FOR_DELIVERY': 'READY_FOR_PICKUP', 'IN_TRANSIT': 'HANDED_OVER',
                'DELIVERED': 'HANDED_OVER', 'CANCELLED': 'CANCELLED',
            }[status]
            for seller_id in seller_ids:
                OrderFulfillment.objects.create(order=order, seller_id=seller_id, status=fulfillment_status,
                                                fulfill_by=created_at + timedelta(days=2))
            orders.append(order)

        # Backfill legacy demo orders that predate multi-seller line items.
        active_products = [product for product in products if product.status == 'ACTIVE']
        for order in Order.objects.filter(items__isnull=True):
            product = random.choice(active_products)
            quantity = random.randrange(1, 3)
            OrderItem.objects.create(order=order, product=product, seller=product.seller,
                                     quantity=quantity, price_snapshot=product.price)
            subtotal = product.price * quantity
            order.product_subtotal = subtotal
            order.total_amount = subtotal
            order.save(update_fields=['product_subtotal', 'total_amount'])
            OrderFulfillment.objects.get_or_create(order=order, seller=product.seller, defaults={
                'status': 'CANCELLED' if order.status == 'CANCELLED' else 'HANDED_OVER' if order.status in {'IN_TRANSIT', 'DELIVERED'} else 'ACCEPTED',
                'fulfill_by': order.created_at + timedelta(days=2),
            })
        
        self.stdout.write(self.style.SUCCESS(f'Created {orders_to_create} orders; total is {Order.objects.count()}'))

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
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(reviews)} reviews'))

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
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(notifications)} notifications'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('SEEDING COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Categories: {Category.objects.count()}')
        self.stdout.write(f'Users: {User.objects.count()} (Buyers: {User.objects.filter(role="BUYER").count()}, Sellers: {User.objects.filter(role="SELLER").count()})')
        self.stdout.write(f'Sellers: {Seller.objects.count()} (Verified: {Seller.objects.filter(verified=True).count()})')
        self.stdout.write(f'Products: {Product.objects.count()} (Active: {Product.objects.filter(status="ACTIVE").count()}, Pending: {Product.objects.filter(status="PENDING_APPROVAL").count()})')
        self.stdout.write(f'Orders: {Order.objects.count()}')
        self.stdout.write(f'Reviews: {Review.objects.count()}')
        self.stdout.write(f'Notifications: {Notification.objects.count()}')
        self.stdout.write(self.style.SUCCESS('='*50))
        
        self.stdout.write(self.style.WARNING('\nTest Credentials:'))
        self.stdout.write('  Buyer: john_buyer / buyer123')
        self.stdout.write('  Seller: techstore / seller123')
