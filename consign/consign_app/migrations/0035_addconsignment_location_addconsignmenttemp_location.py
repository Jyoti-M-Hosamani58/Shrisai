# Generated by Django 5.0.6 on 2024-10-10 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consign_app', '0034_alter_location_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='addconsignment',
            name='location',
            field=models.CharField(max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='addconsignmenttemp',
            name='location',
            field=models.CharField(max_length=150, null=True),
        ),
    ]
