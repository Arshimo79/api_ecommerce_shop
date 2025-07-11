# Generated by Django 4.2.5 on 2025-05-27 21:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shop', '0009_alter_wishlist_options_wishlistitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShippingMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shipping_method', models.CharField(max_length=50)),
                ('price', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('delivery_time', models.DurationField()),
                ('shipping_method_active', models.BooleanField(default=True)),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('datetime_modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receiver_name', models.CharField(max_length=100)),
                ('receiver_family', models.CharField(max_length=150)),
                ('receiver_phone_number', models.CharField(max_length=13)),
                ('receiver_city', models.CharField(choices=[('Tehran', 'Tehran'), ('Karaj', 'Karaj')], max_length=85)),
                ('receiver_address', models.TextField()),
                ('receiver_postal_code', models.CharField(max_length=20)),
                ('receiver_latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('receiver_longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('datetime_modified', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': '9. Addresses',
            },
        ),
    ]
