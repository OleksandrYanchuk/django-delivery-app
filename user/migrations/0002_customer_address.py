# Generated by Django 4.2.2 on 2023-09-28 07:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="address",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
