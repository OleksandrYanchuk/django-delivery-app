# Generated by Django 4.2.2 on 2023-10-04 07:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0002_alter_order_total_with_discount"),
    ]

    operations = [
        migrations.AddField(
            model_name="discountcoupon",
            name="expiration_datetime",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
