# Generated by Django 4.2.5 on 2024-08-23 08:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0007_remove_order_datetime_modified_order_status_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wishlist',
            name='product',
        ),
    ]
