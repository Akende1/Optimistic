from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='company_name',
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name='order',
            name='company_tax_id',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='order',
            name='order_type',
            field=models.CharField(choices=[('RETAIL', 'Retail'), ('PURCHASE_ORDER', 'Purchase Order')], db_index=True, default='RETAIL', max_length=20),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_terms',
            field=models.CharField(blank=True, help_text='e.g., NET_30, NET_45, COD', max_length=80),
        ),
        migrations.AddField(
            model_name='order',
            name='po_number',
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddField(
            model_name='order',
            name='procurement_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='order',
            name='requested_fulfillment_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
