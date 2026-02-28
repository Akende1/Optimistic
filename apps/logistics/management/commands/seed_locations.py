"""
Management command to seed Zambian locations (provinces, cities, zones)
Usage: python manage.py seed_locations
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.logistics.models import ZambianLocation


class Command(BaseCommand):
    help = 'Seeds Zambian provinces, cities, and delivery zones'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting location seeding...'))

        # Create Provinces
        self.stdout.write('Creating provinces...')
        provinces_data = [
            ('Lusaka', 20),
            ('Copperbelt', 30),
            ('Southern', 40),
            ('Eastern', 45),
            ('Western', 50),
            ('Northern', 55),
            ('North-Western', 60),
            ('Luapula', 60),
            ('Muchinga', 65),
            ('Central', 35),
        ]

        provinces = {}
        for name, base_cost in provinces_data:
            province, created = ZambianLocation.objects.get_or_create(
                name=name,
                location_type='PROVINCE',
                defaults={
                    'delivery_base_cost': Decimal(str(base_cost)),
                    'is_active': True
                }
            )
            provinces[name] = province

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(provinces)} provinces'))

        # Create Cities
        self.stdout.write('Creating cities...')
        cities_data = [
            # Lusaka Province
            ('Lusaka', 'Lusaka', 15),
            ('Kafue', 'Lusaka', 25),
            ('Chongwe', 'Lusaka', 30),
            
            # Copperbelt
            ('Ndola', 'Copperbelt', 25),
            ('Kitwe', 'Copperbelt', 25),
            ('Chingola', 'Copperbelt', 30),
            ('Mufulira', 'Copperbelt', 30),
            ('Luanshya', 'Copperbelt', 30),
            
            # Southern
            ('Livingstone', 'Southern', 35),
            ('Choma', 'Southern', 40),
            ('Mazabuka', 'Southern', 35),
            
            # Eastern
            ('Chipata', 'Eastern', 40),
            ('Petauke', 'Eastern', 45),
            
            # Western
            ('Mongu', 'Western', 50),
            ('Senanga', 'Western', 55),
            
            # Northern
            ('Kasama', 'Northern', 50),
            ('Mbala', 'Northern', 55),
            
            # Central
            ('Kabwe', 'Central', 30),
            ('Kapiri Mposhi', 'Central', 35),
        ]

        cities = {}
        for city_name, province_name, base_cost in cities_data:
            city, created = ZambianLocation.objects.get_or_create(
                name=city_name,
                location_type='CITY',
                parent=provinces[province_name],
                defaults={
                    'delivery_base_cost': Decimal(str(base_cost)),
                    'is_active': True
                }
            )
            cities[city_name] = city

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(cities)} cities'))

        # Create Zones (focusing on Lusaka for now)
        self.stdout.write('Creating zones...')
        lusaka_zones = [
            ('Lusaka CBD', 10),
            ('Kabulonga', 15),
            ('Woodlands', 12),
            ('Roma', 12),
            ('Makeni', 15),
            ('Chelston', 12),
            ('Chilenje', 12),
            ('Kalingalinga', 15),
            ('Garden Compound', 15),
            ('Chaisa', 20),
            ('Chawama', 18),
            ('Matero', 15),
            ('Northmead', 12),
            ('Avondale', 15),
            ('Kalundu', 18),
            ('Lilayi', 25),
            ('PHI', 20),
            ('Meanwood', 15),
        ]

        ndola_zones = [
            ('Ndola CBD', 20),
            ('Kansenshi', 22),
            ('Northrise', 22),
            ('Itawa', 25),
            ('Masala', 23),
        ]

        kitwe_zones = [
            ('Kitwe CBD', 20),
            ('Riverside', 22),
            ('Parklands', 22),
            ('Garneton', 23),
            ('Wusakile', 23),
        ]

        zones_created = 0

        for zone_name, base_cost in lusaka_zones:
            zone, created = ZambianLocation.objects.get_or_create(
                name=zone_name,
                location_type='ZONE',
                parent=cities['Lusaka'],
                defaults={
                    'delivery_base_cost': Decimal(str(base_cost)),
                    'is_active': True
                }
            )
            if created:
                zones_created += 1

        for zone_name, base_cost in ndola_zones:
            zone, created = ZambianLocation.objects.get_or_create(
                name=zone_name,
                location_type='ZONE',
                parent=cities['Ndola'],
                defaults={
                    'delivery_base_cost': Decimal(str(base_cost)),
                    'is_active': True
                }
            )
            if created:
                zones_created += 1

        for zone_name, base_cost in kitwe_zones:
            zone, created = ZambianLocation.objects.get_or_create(
                name=zone_name,
                location_type='ZONE',
                parent=cities['Kitwe'],
                defaults={
                    'delivery_base_cost': Decimal(str(base_cost)),
                    'is_active': True
                }
            )
            if created:
                zones_created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Created {zones_created} zones'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('✅ LOCATION SEEDING COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'📍 Total Locations: {ZambianLocation.objects.count()}')
        self.stdout.write(f'   - Provinces: {ZambianLocation.objects.filter(location_type="PROVINCE").count()}')
        self.stdout.write(f'   - Cities: {ZambianLocation.objects.filter(location_type="CITY").count()}')
        self.stdout.write(f'   - Zones: {ZambianLocation.objects.filter(location_type="ZONE").count()}')
        self.stdout.write(self.style.SUCCESS('='*50))
