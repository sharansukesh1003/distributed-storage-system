# Generated by Django 5.1.7 on 2025-03-16 21:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StoredFile',
            fields=[
                ('file_size', models.BigIntegerField()),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('file_id', models.CharField(max_length=255)),
                ('file_name', models.CharField(max_length=255)),
                ('file_path', models.CharField(max_length=500)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='FileChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chunk_number', models.IntegerField()),
                ('chunk_size', models.BigIntegerField()),
                ('chunk_path', models.CharField(max_length=500)),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='storage_app.storedfile')),
            ],
        ),
    ]
