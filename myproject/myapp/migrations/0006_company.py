# Generated by Django 5.2 on 2025-05-04 21:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_person_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('C_name', models.CharField(max_length=100)),
                ('address', models.CharField(max_length=255)),
                ('phone_number', models.CharField(max_length=15)),
                ('email', models.EmailField(max_length=100)),
            ],
        ),
    ]
