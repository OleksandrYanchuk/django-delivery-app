# Generated by Django 4.2.2 on 2023-10-03 11:10

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="total_with_discount",
            field=models.DecimalField(
                blank=True, decimal_places=2, default=None, max_digits=10, null=True
            ),
        ),
    ]
