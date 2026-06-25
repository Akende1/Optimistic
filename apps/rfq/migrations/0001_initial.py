import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('products', '0002_product_attributes'),
        ('sellers', '0003_seller_primary_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='RfqRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=180)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('AWARDED', 'Awarded'), ('CLOSED', 'Closed'), ('EXPIRED', 'Expired')], db_index=True, default='OPEN', max_length=20)),
                ('incoterm', models.CharField(choices=[('EXW', 'Ex Works'), ('FOB', 'Free On Board'), ('CIF', 'Cost Insurance Freight'), ('DDP', 'Delivered Duty Paid'), ('OTHER', 'Other')], default='OTHER', max_length=12)),
                ('delivery_location', models.CharField(blank=True, max_length=180)),
                ('is_sample_required', models.BooleanField(default=False)),
                ('response_deadline', models.DateTimeField(db_index=True)),
                ('desired_delivery_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rfq_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RfqItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=220)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('target_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('unit', models.CharField(default='unit', max_length=40)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rfq_items', to='products.category')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rfq_items', to='products.product')),
                ('rfq', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='rfq.rfqrequest')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='SupplierQuote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('SUBMITTED', 'Submitted'), ('WON', 'Won'), ('LOST', 'Lost'), ('WITHDRAWN', 'Withdrawn')], db_index=True, default='SUBMITTED', max_length=20)),
                ('lead_time_days', models.PositiveIntegerField(default=7)),
                ('notes', models.TextField(blank=True)),
                ('valid_until', models.DateField(blank=True, null=True)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rfq', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quotes', to='rfq.rfqrequest')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rfq_quotes', to='sellers.seller')),
            ],
            options={
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.CreateModel(
            name='SupplierQuoteItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=220)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('moq', models.PositiveIntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quote_items', to='products.product')),
                ('quote', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='rfq.supplierquote')),
                ('rfq_item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quote_items', to='rfq.rfqitem')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.AddField(
            model_name='rfqrequest',
            name='awarded_quote',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='awarded_rfqs', to='rfq.supplierquote'),
        ),
        migrations.AddConstraint(
            model_name='supplierquote',
            constraint=models.UniqueConstraint(fields=('rfq', 'seller'), name='unique_quote_per_seller_per_rfq'),
        ),
    ]
