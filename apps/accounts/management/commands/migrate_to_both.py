from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.sellers.models import Seller
import csv
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Convert eligible users to seller-capable role (dry-run by default). Generates CSV of affected users.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Apply changes (mutates user roles).')
        parser.add_argument('--csv', type=str, help='Path to output CSV report (default: migrate_to_both_report.csv)')

    def handle(self, *args, **options):
        apply_changes = options.get('apply', False)
        csv_path = options.get('csv') or 'migrate_to_both_report.csv'

        candidates = []
        for user in User.objects.all():
            has_seller = Seller.objects.filter(user=user).exists()
            # Candidate when user has a Seller row but role is not SELLER
            if has_seller and user.role != 'SELLER':
                candidates.append((user, has_seller))

        if not candidates:
            self.stdout.write(self.style.SUCCESS('No candidates found. Nothing to do.'))
            return

        # Write CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow(['user_id', 'username', 'email', 'phone_number', 'current_role', 'has_seller'])
            for user, has_seller in candidates:
                writer.writerow([user.id, user.username, user.email, user.phone_number or '', user.role, has_seller])

        self.stdout.write(self.style.NOTICE(f'Wrote report to {csv_path} (candidates: {len(candidates)})'))

        if not apply_changes:
            self.stdout.write(self.style.WARNING('Dry-run complete. No changes applied. Re-run with --apply to update roles.'))
            return

        # Apply changes
        with transaction.atomic():
            updated = 0
            for user, _ in candidates:
                user.role = 'SELLER'
                user.save(update_fields=['role'])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Applied changes to {updated} users.'))
