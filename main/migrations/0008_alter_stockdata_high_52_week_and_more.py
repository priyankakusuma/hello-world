# Generated by Django 5.1.4 on 2025-01-25 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_nsedata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockdata',
            name='high_52_week',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='stockdata',
            name='low_52_week',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
