from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_buyeraddress_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False, help_text='Email address verified via one-time code'),
        ),
        migrations.AddField(
            model_name='user',
            name='email_verified_at',
            field=models.DateTimeField(blank=True, help_text='When email was verified', null=True),
        ),
        migrations.CreateModel(
            name='AccountVerificationCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('PHONE', 'Phone'), ('EMAIL', 'Email')], db_index=True, max_length=10)),
                ('purpose', models.CharField(choices=[('ACCOUNT_VERIFICATION', 'Account Verification')], db_index=True, default='ACCOUNT_VERIFICATION', max_length=30)),
                ('code', models.CharField(max_length=6)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('max_attempts', models.PositiveSmallIntegerField(default=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verification_codes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Account Verification Code',
                'verbose_name_plural': 'Account Verification Codes',
                'ordering': ['-created_at'],
            },
        ),
    ]
