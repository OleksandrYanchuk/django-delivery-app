# Generated by Django 4.2.2 on 2023-09-29 10:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0002_customer_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="user_lat",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="customer",
            name="user_lng",
            field=models.FloatField(blank=True, null=True),
        ),
    ]