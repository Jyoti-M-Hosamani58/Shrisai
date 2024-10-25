# Generated by Django 5.0.6 on 2024-10-10 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consign_app', '0036_consignee_location_consignor_location'),
    ]

    operations = [
        migrations.RenameField(
            model_name='addconsignment',
            old_name='location',
            new_name='receiver_location',
        ),
        migrations.RenameField(
            model_name='addconsignmenttemp',
            old_name='location',
            new_name='receiver_location',
        ),
        migrations.AddField(
            model_name='addconsignment',
            name='sender_location',
            field=models.CharField(max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='addconsignmenttemp',
            name='sender_location',
            field=models.CharField(max_length=150, null=True),
        ),
    ]