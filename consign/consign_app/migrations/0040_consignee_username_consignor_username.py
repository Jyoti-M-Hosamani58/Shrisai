# Generated by Django 5.0.6 on 2024-10-15 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consign_app', '0039_remove_consignee_location_remove_consignor_location_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='consignee',
            name='username',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='consignor',
            name='username',
            field=models.CharField(max_length=250, null=True),
        ),
    ]
