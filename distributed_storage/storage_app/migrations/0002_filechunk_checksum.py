# Generated by Django 5.1.7 on 2025-03-16 21:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='filechunk',
            name='checksum',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
