# Generated by Django 4.2.5 on 2024-08-20 22:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_remove_cart_session_id_remove_cart_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productattribute',
            name='discounted_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
